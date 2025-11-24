"""Claude API client for intelligent content generation."""

import json
import logging
from typing import Any, Optional

import anthropic
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


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


    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Generate text content using Claude.

        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt for context.
            model: Optional model override.
            max_tokens: Optional max tokens override.
            temperature: Temperature for generation (0-1).

        Returns:
            Generated text content or None on failure.
        """
        try:
            response = await self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.content
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None


def get_claude_client() -> ClaudeClient:
    """Get Claude client instance."""
    return ClaudeClient()


def create_claude_client() -> ClaudeClient:
    """Create a new Claude client instance."""
    return ClaudeClient()
