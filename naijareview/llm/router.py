"""Two-tier LLM router: Gemini 2.5 Pro for generation, Gemini 2.0 Flash for utility.

Backed by LangChain's ChatGoogleGenerativeAI so every caller can compose
standard LangChain chains:

    chain = some_prompt | router.generation_llm | StrOutputParser()

The .call() / .call_with_retry() methods remain for callers that just want a str.

See §11.1 and §11.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import logging
from time import sleep
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from naijareview.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Route LLM calls to the appropriate tier with retry logic.

    Exposes two public LangChain model instances for direct chain composition:
        router.generation_llm  — Gemini 2.5 Pro  (Sonnet equivalent)
        router.utility_llm     — Gemini 2.0 Flash (Haiku equivalent)
    """

    def __init__(self) -> None:
        self.generation_llm = ChatGoogleGenerativeAI(
            model=settings.gemini_generation_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.llm_default_temperature,
            max_output_tokens=settings.llm_max_tokens,
        )
        self.utility_llm = ChatGoogleGenerativeAI(
            model=settings.gemini_utility_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.llm_default_temperature,
            max_output_tokens=settings.llm_max_tokens,
        )

    def get_llm(
        self,
        tier: Literal["generation", "utility"],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatGoogleGenerativeAI:
        """Return the LangChain model for the given tier.

        Optionally rebind temperature / max_tokens for this call without
        mutating the shared instance.
        """
        base = self.generation_llm if tier == "generation" else self.utility_llm
        overrides: dict = {}
        if temperature is not None:
            overrides["temperature"] = temperature
        if max_tokens is not None:
            overrides["max_output_tokens"] = max_tokens
        return base.bind(**overrides) if overrides else base  # type: ignore[return-value]

    def call(
        self,
        tier: Literal["generation", "utility"],
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Single LLM call → str.

        Routing rules (§11.2):
        - generation: review drafts, reranking, explanations  → Gemini 2.5 Pro
        - utility:    item analysis, vibe checks, cold-start  → Gemini 2.0 Flash
        """
        llm = self.get_llm(tier, temperature=temperature, max_tokens=max_tokens)
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)

    def call_with_retry(
        self,
        tier: Literal["generation", "utility"],
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        max_retries: int = 2,
    ) -> str:
        """call() with exponential backoff on rate-limit / server errors."""
        for attempt in range(max_retries + 1):
            try:
                return self.call(tier, prompt, max_tokens, temperature)
            except Exception as exc:
                err = str(exc).lower()
                is_rate = "429" in err or "quota" in err or "rate" in err
                is_server = "500" in err or "503" in err or "server" in err

                if (is_rate or is_server) and attempt < max_retries:
                    wait = 2**attempt
                    logger.warning(
                        "LLM error (%s), retry %d/%d in %ds",
                        type(exc).__name__,
                        attempt + 1,
                        max_retries,
                        wait,
                    )
                    sleep(wait)
                    continue
                raise

        raise RuntimeError("Exhausted retries")
