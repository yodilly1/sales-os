"""
Claude API Client

Provides a unified interface for interacting with Claude AI
for SPICED analysis, coaching, and content generation.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Client for interacting with the Claude API.

    Handles authentication, request formatting, and response parsing
    for all Claude API interactions within Sales OS.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_MAX_TOKENS = 4096
    API_BASE_URL = "https://api.anthropic.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ):
        """
        Initialize the Claude client.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
            model: Model to use. Defaults to claude-sonnet-4-20250514.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout

        if not self.api_key:
            logger.warning("No ANTHROPIC_API_KEY provided. Claude API calls will fail.")

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a completion from Claude.

        Args:
            prompt: The user prompt to send
            system: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            stop_sequences: Optional sequences to stop generation

        Returns:
            The generated text response

        Raises:
            ClaudeAPIError: If the API request fails
        """
        if not self.api_key:
            raise ClaudeAPIError("No API key configured")

        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        if system:
            payload["system"] = system

        if stop_sequences:
            payload["stop_sequences"] = stop_sequences

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

                # Extract text from response
                content = data.get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "")

                return ""

        except httpx.TimeoutException as e:
            logger.error(f"Claude API timeout: {e}")
            raise ClaudeAPIError(f"Request timed out: {e}") from e

        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API HTTP error: {e}")
            raise ClaudeAPIError(f"HTTP error: {e.response.status_code}") from e

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeAPIError(f"API error: {e}") from e

    async def complete_with_context(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a completion with conversation context.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            The generated text response
        """
        if not self.api_key:
            raise ClaudeAPIError("No API key configured")

        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/messages",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

                content = data.get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "")

                return ""

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeAPIError(f"API error: {e}") from e

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.

        This is a rough estimate - actual token counts may vary.

        Args:
            text: The text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token on average
        return len(text) // 4


class ClaudeAPIError(Exception):
    """Exception raised for Claude API errors."""

    pass
