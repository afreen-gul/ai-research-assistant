"""Writing agent — drafts research documents from gathered sources."""

import logging
from typing import Any

from prompts.system_prompts import WRITING_AGENT_SYSTEM
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

DOC_TYPE_PROMPTS = {
    "summary": "Write a concise research summary covering key findings, main themes, and conclusions.",
    "literature_review": (
        "Write a thematic literature review. Group sources by theme/topic, identify trends, "
        "compare methodologies, and highlight research gaps. Use clear section headings."
    ),
    "comparison": (
        "Create a detailed comparison of the tools/models/approaches found in the sources. "
        "Include a markdown comparison table with relevant criteria."
    ),
    "report": (
        "Write a full research report with: Executive Summary, Introduction, Background, "
        "Findings, Analysis, Conclusions, and Recommendations sections."
    ),
    "paper_draft": (
        "Draft an academic paper with sections: Abstract, Introduction, Literature Review, "
        "Methodology, Proposed System/Approach, Results/Discussion, Conclusion, and Future Work."
    ),
}


class WritingAgent:
    def __init__(self) -> None:
        self.llm = get_llm_service()

    async def draft(
        self,
        doc_type: str,
        topic: str,
        sources: list[dict[str, Any]],
        research_findings: str = "",
        citation_style: str = "apa",
    ) -> dict[str, Any]:
        doc_type = doc_type if doc_type in DOC_TYPE_PROMPTS else "summary"
        type_instruction = DOC_TYPE_PROMPTS[doc_type]

        sources_text = ""
        for i, src in enumerate(sources, 1):
            sources_text += (
                f"\n[{i}] {src.get('title', 'Untitled')}\n"
                f"    URL: {src.get('url', 'N/A')}\n"
                f"    Authors: {src.get('authors', 'Unknown')}\n"
                f"    Snippet: {src.get('snippet', src.get('body', ''))[:300]}\n"
            )

        messages = [
            {"role": "system", "content": WRITING_AGENT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    f"Document type: {doc_type}\n"
                    f"Instruction: {type_instruction}\n"
                    f"Citation style: {citation_style.upper()}\n\n"
                    f"Research findings from the research agent:\n{research_findings}\n\n"
                    f"Available sources (ONLY cite these):\n{sources_text}\n\n"
                    f"Write the document now. Use [1], [2], etc. for in-text citations."
                ),
            },
        ]

        logger.info("Writing agent drafting %s for topic: %s", doc_type, topic)
        content = await self.llm.generate(messages, temperature=0.4)

        return {
            "content": content,
            "doc_type": doc_type,
            "title": f"{doc_type.replace('_', ' ').title()}: {topic[:80]}",
            "citation_style": citation_style,
        }
