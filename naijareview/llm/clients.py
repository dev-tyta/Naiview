"""Anthropic client wrappers + retry logic.

Low-level client configuration. The LLMRouter in router.py is the
public-facing interface — prefer using that.
"""

from __future__ import annotations

# The router.py module handles all client interactions.
# This file exists for any future client-level customisation
# (e.g., custom transport, mock clients for testing).
