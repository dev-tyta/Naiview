"""Two-tier LLM router: Gemini 2.5 Pro for generation, Gemini 2.0 Flash for utility.
11.1 and 11.2 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import logging
from time import sleep
from typing import Literal

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
from google.generativeai.types import GenerationConfig

from naijareview.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Route LLM calls to the appropriate tier with retry logic."""

    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._generation_model = genai.GenerativeModel(
            model_name=settings.gemini_generation_model,
        )
        self._utility_model = genai.GenerativeModel(
            model_name=settings.gemini_utility_model,
        )

    def call(
        self,
        tier: Literal["generation", "utility"],
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Make a single LLM call to the appropriate tier.

        Routing rules (§11.2):
        - generation tier (Gemini 2.5 Pro): review drafts, reranking, explanations
        - utility tier (Gemini 2.0 Flash): item analysis, vibe checks, cold-start parsing
        """
        model = self._generation_model if tier == "generation" else self._utility_model
        config = GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = model.generate_content(prompt, generation_config=config)
        return response.text

    def call_with_retry(
        self,
        tier: Literal["generation", "utility"],
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        max_retries: int = 2,
    ) -> str:
        """Call with exponential backoff retry on rate-limit and API errors."""
        for attempt in range(max_retries + 1):
            try:
                return self.call(tier, prompt, max_tokens, temperature)
            except ResourceExhausted:
                if attempt < max_retries:
                    wait = 2**attempt
                    logger.warning(
                        "Rate limited, retrying in %ds (attempt %d/%d)",
                        wait,
                        attempt + 1,
                        max_retries,
                    )
                    sleep(wait)
                    continue
                raise
            except GoogleAPIError:
                if attempt < max_retries:
                    logger.warning(
                        "API error, retrying (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )
                    continue
                raise
        msg = "Exhausted retries"
        raise RuntimeError(msg)
