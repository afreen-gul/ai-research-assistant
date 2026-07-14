"""Review agent — grammar, clarity, and consistency pass on drafts."""

import logging

from prompts.system_prompts import REVIEW_AGENT_SYSTEM
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class ReviewAgent:
    def __init__(self) -> None:
        self.llm = get_llm_service()

    async def review(self, draft: str) -> str:
        messages = [
            {"role": "system", "content": REVIEW_AGENT_SYSTEM},
            {"role": "user", "content": f"Review and polish this document:\n\n{draft}"},
        ]
        logger.info("Review agent polishing draft (%d chars)", len(draft))
        return await self.llm.generate(messages, temperature=0.2)
