"""LLM service abstraction — swap providers without touching the rest of the app."""

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your_xai_api_key_here",
    "your_groq_api_key_here",
    "your_openai_api_key_here",
    "change-me",
    "placeholder",
}

_PROVIDER_KEY_HELP = {
    "gemini": (
        "GEMINI_API_KEY",
        "https://aistudio.google.com/apikey",
    ),
    "xai": (
        "XAI_API_KEY",
        "https://console.x.ai/",
    ),
    "groq": (
        "GROQ_API_KEY",
        "https://console.groq.com/keys",
    ),
    "openai": (
        "OPENAI_API_KEY",
        "https://platform.openai.com/api-keys",
    ),
}


class MissingAPIKeyError(RuntimeError):
    """Raised when an LLM call is attempted without a configured API key."""


def _is_placeholder(key: str) -> bool:
    return (key or "").strip().lower() in _PLACEHOLDER_KEYS


def _require_api_key(provider: str, key: str) -> str:
    env_name, signup_url = _PROVIDER_KEY_HELP.get(provider, ("API key", ""))
    cleaned = (key or "").strip()
    if _is_placeholder(cleaned):
        raise MissingAPIKeyError(
            f"{env_name} is not configured for LLM_PROVIDER={provider}. "
            f"Add your key from {signup_url} to the .env file and restart the backend."
        )
    return cleaned


class LLMService(ABC):
    provider: str = "unknown"
    model_name: str = ""

    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        ...

    @abstractmethod
    def get_chat_model(self, **kwargs: Any) -> Any:
        ...

    def is_configured(self) -> bool:
        return False


def _to_langchain_messages(messages: list[dict[str, str]]) -> list[BaseMessage]:
    result: list[BaseMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            result.append(SystemMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
        else:
            result.append(HumanMessage(content=content))
    return result


class GeminiLLMService(LLMService):
    provider = "gemini"

    def __init__(self) -> None:
        self.model_name = settings.gemini_model
        if _is_placeholder(settings.gemini_api_key):
            logger.warning("GEMINI_API_KEY not set — LLM calls will fail")

    def is_configured(self) -> bool:
        return not _is_placeholder(settings.gemini_api_key)

    def get_chat_model(self, **kwargs: Any) -> ChatGoogleGenerativeAI:
        api_key = _require_api_key(self.provider, settings.gemini_api_key)
        return ChatGoogleGenerativeAI(
            model=kwargs.get("model", self.model_name),
            google_api_key=api_key,
            temperature=kwargs.get("temperature", 0.3),
            max_output_tokens=kwargs.get("max_output_tokens", 8192),
            max_retries=0,
        )

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        llm = self.get_chat_model(**kwargs)
        lc_messages = _to_langchain_messages(messages)
        logger.info("LLM generate call (%s) with %d messages", self.provider, len(messages))
        try:
            response = await llm.ainvoke(lc_messages)
            return str(response.content)
        except Exception:
            logger.exception("LLM generation failed")
            raise


class GroqLLMService(LLMService):
    provider = "groq"

    def __init__(self) -> None:
        self.model_name = settings.groq_model
        if _is_placeholder(settings.groq_api_key):
            logger.warning("GROQ_API_KEY not set — LLM calls will fail")

    def is_configured(self) -> bool:
        return not _is_placeholder(settings.groq_api_key)

    def get_chat_model(self, **kwargs: Any) -> Any:
        from langchain_groq import ChatGroq

        api_key = _require_api_key(self.provider, settings.groq_api_key)
        return ChatGroq(
            model=kwargs.get("model", self.model_name),
            groq_api_key=api_key,
            temperature=kwargs.get("temperature", 0.3),
            max_retries=0,
        )

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        llm = self.get_chat_model(**kwargs)
        lc_messages = _to_langchain_messages(messages)
        logger.info("LLM generate call (%s) with %d messages", self.provider, len(messages))
        try:
            response = await llm.ainvoke(lc_messages)
            return str(response.content)
        except Exception:
            logger.exception("LLM generation failed")
            raise


class XAILLMService(LLMService):
    provider = "xai"

    def __init__(self) -> None:
        self.model_name = settings.xai_model
        if _is_placeholder(settings.xai_api_key):
            logger.warning("XAI_API_KEY not set — LLM calls will fail")

    def is_configured(self) -> bool:
        return not _is_placeholder(settings.xai_api_key)

    def get_chat_model(self, **kwargs: Any) -> Any:
        from langchain_xai import ChatXAI

        api_key = _require_api_key(self.provider, settings.xai_api_key)
        return ChatXAI(
            model=kwargs.get("model", self.model_name),
            xai_api_key=api_key,
            temperature=kwargs.get("temperature", 0.3),
            max_retries=0,
        )

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        llm = self.get_chat_model(**kwargs)
        lc_messages = _to_langchain_messages(messages)
        logger.info("LLM generate call (%s) with %d messages", self.provider, len(messages))
        try:
            response = await llm.ainvoke(lc_messages)
            return str(response.content)
        except Exception:
            logger.exception("LLM generation failed")
            raise


class OpenAILLMService(LLMService):
    provider = "openai"

    def __init__(self) -> None:
        self.model_name = settings.openai_model
        if _is_placeholder(settings.openai_api_key):
            logger.warning("OPENAI_API_KEY not set — LLM calls will fail")

    def is_configured(self) -> bool:
        return not _is_placeholder(settings.openai_api_key)

    def get_chat_model(self, **kwargs: Any) -> Any:
        from langchain_openai import ChatOpenAI

        api_key = _require_api_key(self.provider, settings.openai_api_key)
        return ChatOpenAI(
            model=kwargs.get("model", self.model_name),
            api_key=api_key,
            temperature=kwargs.get("temperature", 0.3),
            max_retries=0,
        )

    async def generate(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        llm = self.get_chat_model(**kwargs)
        lc_messages = _to_langchain_messages(messages)
        logger.info("LLM generate call (%s) with %d messages", self.provider, len(messages))
        try:
            response = await llm.ainvoke(lc_messages)
            return str(response.content)
        except Exception:
            logger.exception("LLM generation failed")
            raise


_PROVIDERS: dict[str, type[LLMService]] = {
    "gemini": GeminiLLMService,
    "xai": XAILLMService,
    "groq": GroqLLMService,
    "openai": OpenAILLMService,
}

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        provider = (settings.llm_provider or "gemini").lower().strip()
        service_cls = _PROVIDERS.get(provider)
        if service_cls is None:
            supported = ", ".join(sorted(_PROVIDERS))
            raise ValueError(
                f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Supported: {supported}"
            )
        _llm_service = service_cls()
        logger.info("Using LLM provider=%s model=%s", _llm_service.provider, _llm_service.model_name)
    return _llm_service


def get_llm_status() -> dict[str, Any]:
    service = get_llm_service()
    return {
        "provider": service.provider,
        "model": service.model_name,
        "configured": service.is_configured(),
    }
