<<<<<<< HEAD
"""Claude API client for intelligent content generation."""

import json
import logging
from typing import Any, Optional

import anthropic
from pydantic import BaseModel

from app.core.config import get_settings
=======
"""
Claude API Client

Provides a unified interface for interacting with Claude AI
for SPICED analysis, coaching, and content generation.
"""

import logging
import os
from typing import Optional

import httpx
>>>>>>> origin/claude/spiced-coaching-module-01AiTWp9Wpsm2vQQXbEqCfvu

logger = logging.getLogger(__name__)


<<<<<<< HEAD
class ClaudeResponse(BaseModel):
    """Response from Claude API."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude client.

        Args:
            api_key: Optional API key. If not provided, uses config.
        """
        settings = get_settings()
        self.api_key = api_key or settings.claude_api_key
        self.default_model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens

        if not self.api_key:
            logger.warning("Claude API key not configured")

        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Get or create the Anthropic client."""
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> ClaudeResponse:
        """Generate content using Claude.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.
            model: Optional model override.
            max_tokens: Optional max tokens override.
            temperature: Temperature for generation (0-1).

        Returns:
            ClaudeResponse with generated content and metadata.
        """
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
            )

            return ClaudeResponse(
                content=message.content[0].text,
                model=message.model,
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                stop_reason=message.stop_reason,
            )

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Claude: {e}")
            raise

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> tuple[dict[str, Any], ClaudeResponse]:
        """Generate JSON content using Claude.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.
            model: Optional model override.
            max_tokens: Optional max tokens override.
            temperature: Temperature for generation (lower for structured output).

        Returns:
            Tuple of (parsed JSON dict, ClaudeResponse).
        """
        # Enhance prompt to request JSON output
        json_prompt = f"""{prompt}

IMPORTANT: Return your response as valid JSON only. Do not include any text before or after the JSON.
Do not wrap the JSON in markdown code blocks."""

        response = await self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Parse JSON from response
        try:
            # Try to extract JSON if wrapped in code blocks
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            parsed = json.loads(content)
            return parsed, response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Raw response: {response.content[:500]}...")
            raise ValueError(f"Claude returned invalid JSON: {e}")

    async def generate_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs,
    ) -> ClaudeResponse:
        """Generate content with automatic retry on failure.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.
            max_retries: Maximum number of retry attempts.
            **kwargs: Additional arguments passed to generate().

        Returns:
            ClaudeResponse with generated content.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs,
                )
            except anthropic.RateLimitError:
                logger.warning(f"Rate limited, attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                import asyncio
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except anthropic.APIError as e:
                last_error = e
                logger.warning(f"API error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise

        raise last_error or RuntimeError("Max retries exceeded")
=======
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
>>>>>>> origin/claude/spiced-coaching-module-01AiTWp9Wpsm2vQQXbEqCfvu
