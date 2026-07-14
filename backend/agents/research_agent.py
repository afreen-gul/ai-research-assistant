"""Research agent — orchestrates search, read, and RAG retrieval via LangGraph."""

import asyncio
import json
import logging
import uuid
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from agents.citation_agent import extract_citation_from_search_result
from config import settings
from prompts.system_prompts import FINALIZE_AGENT_SYSTEM, RESEARCH_AGENT_SYSTEM
from rag.retriever import format_retrieved_context, ingest_document, retrieve_context
from services.llm_service import get_llm_service
from tools.pdf_reader import read_pdf
from tools.search_tool import search_academic, search_web
from tools.web_scraper import scrape_url, summarize_url_content
from tools.youtube_reader import format_transcript_with_timestamps, get_youtube_transcript

logger = logging.getLogger(__name__)

MAX_TOOL_RESULT_CHARS = 6000


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    sources: list[dict[str, Any]]
    tool_events: list[dict[str, str]]
    document_request: dict[str, Any] | None
    tool_rounds: int


def _trim_tool_output(text: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def _message_has_tool_calls(message: Any) -> bool:
    return bool(getattr(message, "tool_calls", None))


def _extract_response_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "\n".join(parts).strip()
    return str(content).strip()


def _collect_tool_events(messages: list[Any]) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                events.append({
                    "tool": tc.get("name", "unknown"),
                    "status": "running",
                    "args": tc.get("args", {}),
                })
        if isinstance(msg, ToolMessage):
            events.append({"tool": msg.name or "unknown", "status": "completed"})
    return events


def _make_tools(session_id: str, sources: list[dict]):
    @tool
    def web_search(query: str) -> str:
        """Search the web for information, papers, articles, GitHub repos, and documentation."""
        results = search_web(query)
        for r in results:
            sources.append(extract_citation_from_search_result(r))
        return _trim_tool_output(json.dumps(results[:8], indent=2))

    @tool
    def academic_search(query: str) -> str:
        """Search for academic papers on arXiv, IEEE, ACM, and GitHub."""
        results = search_academic(query)
        for r in results:
            sources.append(extract_citation_from_search_result(r))
        return _trim_tool_output(json.dumps(results[:6], indent=2))

    @tool
    def read_url(url: str) -> str:
        """Read and extract content from a web page URL."""
        content = scrape_url(url)
        source = extract_citation_from_search_result({
            "title": content.get("title", ""),
            "url": content.get("url", url),
            "domain": content.get("domain", ""),
            "body": content.get("description", ""),
        })
        sources.append(source)
        ingest_document(session_id, content.get("text", ""), source.get("url", url), source.get("title", ""), "web")
        return _trim_tool_output(summarize_url_content(content))

    @tool
    def read_youtube(url: str) -> str:
        """Get transcript from a YouTube video URL for summarization."""
        data = get_youtube_transcript(url)
        source = extract_citation_from_search_result({
            "title": f"YouTube Video {data.get('video_id', '')}",
            "url": url,
            "body": data.get("full_text", "")[:500],
        })
        sources.append(source)
        ingest_document(session_id, data.get("full_text", ""), url, source.get("title", ""), "youtube")
        return _trim_tool_output(format_transcript_with_timestamps(data))

    @tool
    def retrieve_documents(query: str) -> str:
        """Search ingested documents for relevant sections using RAG retrieval."""
        results = retrieve_context(session_id, query)
        return _trim_tool_output(format_retrieved_context(results))

    @tool
    def extract_pdf_info(file_id: str) -> str:
        """Extract structured information from an uploaded PDF by file ID."""
        from config import settings
        from pathlib import Path

        upload_dir = Path(settings.upload_dir)
        pdf_path = None
        for f in upload_dir.glob(f"{file_id}*"):
            if f.suffix.lower() == ".pdf":
                pdf_path = f
                break
        if not pdf_path:
            return f"PDF with ID {file_id} not found. Ask the user to upload it first."

        data = read_pdf(str(pdf_path))
        source = extract_citation_from_search_result({
            "title": data["metadata"].get("title", pdf_path.stem),
            "url": f"upload://{file_id}",
            "author": data["metadata"].get("author", ""),
            "body": data["structured"].get("abstract", ""),
        })
        sources.append(source)
        ingest_document(session_id, data.get("text", ""), file_id, source.get("title", ""), "pdf")
        return _trim_tool_output(json.dumps({"structured": data["structured"], "metadata": data["metadata"]}, indent=2))

    return [web_search, academic_search, read_url, read_youtube, retrieve_documents, extract_pdf_info]


def _detect_document_request(content: str) -> dict[str, Any] | None:
    """Only trigger document panel for explicit document requests."""
    content_lower = content.lower()
    explicit_phrases = {
        "literature review": "literature_review",
        "write a literature review": "literature_review",
        "research report": "report",
        "write a report": "report",
        "comparison of": "comparison",
        "compare the following": "comparison",
        "paper draft": "paper_draft",
        "draft a paper": "paper_draft",
        "write a research summary": "summary",
    }
    for phrase, doc_type in explicit_phrases.items():
        if phrase in content_lower:
            return {"type": doc_type, "requested": True}
    return None


class ResearchAgent:
    def __init__(self) -> None:
        self.llm_service = get_llm_service()

    def _build_graph(self, session_id: str, sources: list[dict]):
        tools = _make_tools(session_id, sources)
        llm = self.llm_service.get_chat_model()
        llm_with_tools = llm.bind_tools(tools)
        llm_plain = self.llm_service.get_chat_model()

        def agent_node(state: AgentState):
            rounds = state.get("tool_rounds", 0)
            system = RESEARCH_AGENT_SYSTEM
            if rounds > 0:
                system += (
                    f"\n\nTool rounds used: {rounds}/{settings.agent_max_tool_rounds}. "
                    "If you have enough information, answer now without more tools."
                )
            messages = [SystemMessage(content=system)] + state["messages"]
            logger.info("LLM call: agent node (tool round %d)", rounds)
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}

        def finalize_node(state: AgentState):
            messages = [SystemMessage(content=FINALIZE_AGENT_SYSTEM)] + state["messages"]
            logger.info("LLM call: finalize node")
            response = llm_plain.invoke(messages)
            return {"messages": [response]}

        def should_continue(state: AgentState) -> Literal["tools", "finalize", "end"]:
            last = state["messages"][-1]
            rounds = state.get("tool_rounds", 0)
            if _message_has_tool_calls(last):
                if rounds >= settings.agent_max_tool_rounds:
                    logger.info("Tool round limit reached (%d); forcing final answer", rounds)
                    return "finalize"
                return "tools"
            return "end"

        tool_node = ToolNode(tools)

        def tool_event_capture(state: AgentState):
            events = list(state.get("tool_events", []))
            rounds = state.get("tool_rounds", 0)
            for msg in reversed(state["messages"]):
                if isinstance(msg, ToolMessage):
                    events.append({"tool": msg.name or "unknown", "status": "completed"})
                elif isinstance(msg, AIMessage) and _message_has_tool_calls(msg):
                    break
            return {"tool_events": events, "tool_rounds": rounds + 1}

        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", tool_node)
        graph.add_node("capture", tool_event_capture)
        graph.add_node("finalize", finalize_node)
        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", "finalize": "finalize", "end": END},
        )
        graph.add_edge("tools", "capture")
        graph.add_edge("capture", "agent")
        graph.add_edge("finalize", END)
        return graph.compile()

    async def _synthesize_final(
        self,
        user_message: str,
        messages: list[Any],
        sources: list[dict[str, Any]],
        note: str = "",
    ) -> str:
        sources_text = "\n".join(
            f"- {s.get('title', 'Untitled')}: {s.get('url', '')}" for s in sources[:10]
        )
        context = "\n".join(
            f"{m.__class__.__name__}: {_extract_response_text(m)[:500]}"
            for m in messages[-8:]
            if _extract_response_text(m)
        )
        prompt = (
            f"{note}\nUser question: {user_message}\n\n"
            f"Gathered sources:\n{sources_text or 'None'}\n\n"
            f"Conversation context:\n{context}\n\n"
            "Write a concise answer using only the gathered information."
        )
        return await self.llm_service.generate(
            [
                {"role": "system", "content": FINALIZE_AGENT_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

    async def run(
        self,
        session_id: str,
        user_message: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        sources: list[dict[str, Any]] = []
        graph = self._build_graph(session_id, sources)

        messages: list[Any] = []
        if history:
            for h in history[-6:]:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    messages.append(AIMessage(content=h["content"]))
        messages.append(HumanMessage(content=user_message))

        doc_request = _detect_document_request(user_message)
        tool_events: list[dict[str, str]] = []

        initial_state: AgentState = {
            "messages": messages,
            "session_id": session_id,
            "sources": sources,
            "tool_events": tool_events,
            "document_request": doc_request,
            "tool_rounds": 0,
        }

        logger.info("Running research agent for session %s", session_id)
        run_config = {"recursion_limit": settings.agent_recursion_limit}

        try:
            final_state = await asyncio.wait_for(
                asyncio.to_thread(graph.invoke, initial_state, run_config),
                timeout=settings.agent_timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Agent timed out after %ss for session %s",
                settings.agent_timeout_seconds,
                session_id,
            )
            response_text = await self._synthesize_final(
                user_message,
                messages,
                sources,
                note="The research step timed out. Summarize what was found so far.",
            )
            return {
                "response": response_text,
                "sources": sources,
                "tool_events": _collect_tool_events(messages),
                "document_request": doc_request,
            }
        except GraphRecursionError:
            logger.warning("Agent hit recursion limit for session %s", session_id)
            response_text = await self._synthesize_final(
                user_message,
                messages,
                sources,
                note="Tool loop limit reached. Summarize gathered findings.",
            )
            return {
                "response": response_text,
                "sources": sources,
                "tool_events": _collect_tool_events(messages),
                "document_request": doc_request,
            }

        last_message = final_state["messages"][-1]
        response_text = _extract_response_text(last_message)

        if not response_text and _message_has_tool_calls(last_message):
            response_text = await self._synthesize_final(
                user_message,
                final_state["messages"],
                sources,
                note="Provide the final answer from gathered tool results.",
            )

        captured_events = _collect_tool_events(final_state["messages"])

        return {
            "response": response_text,
            "sources": sources,
            "tool_events": captured_events,
            "document_request": doc_request,
        }


def ingest_pdf_for_session(session_id: str, file_path: str, file_id: str | None = None) -> dict[str, Any]:
    """Ingest an uploaded PDF into RAG store."""
    file_id = file_id or str(uuid.uuid4())
    data = read_pdf(file_path)
    source = extract_citation_from_search_result({
        "title": data["metadata"].get("title", file_id),
        "url": f"upload://{file_id}",
        "author": data["metadata"].get("author", ""),
    })
    chunk_count = ingest_document(
        session_id, data.get("text", ""), file_id,
        source.get("title", ""), "pdf",
    )
    return {
        "file_id": file_id,
        "structured": data["structured"],
        "metadata": data["metadata"],
        "chunks_ingested": chunk_count,
        "source": source,
    }
