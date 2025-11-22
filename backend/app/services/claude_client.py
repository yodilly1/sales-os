"""Claude API client service for AI-powered analysis."""
import json
import logging
from pathlib import Path
from typing import Any, Optional, TypeVar

from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ClaudeClientError(Exception):
    """Base exception for Claude client errors."""

    pass


class ClaudeAPIError(ClaudeClientError):
    """Error from the Claude API."""

    pass


class ClaudeParseError(ClaudeClientError):
    """Error parsing Claude's response."""

    pass


class ClaudeClient:
    """Client for interacting with Claude API.

    Provides methods for sending prompts and parsing structured responses.
    """

    PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "claude" / "prompts"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key. Defaults to settings.
            model: Model to use. Defaults to settings.
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model

        if not self.api_key:
            raise ClaudeClientError(
                "ANTHROPIC_API_KEY not configured. "
                "Set it in your environment or .env file."
            )

        self.client = Anthropic(api_key=self.api_key)

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from the prompts directory.

        Args:
            prompt_name: Name of the prompt file (without .md extension)

        Returns:
            The prompt template content

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = self.PROMPTS_DIR / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {prompt_path}. "
                f"Available prompts: {list(self.PROMPTS_DIR.glob('*.md'))}"
            )

        return prompt_path.read_text(encoding="utf-8")

    async def analyze(
        self,
        prompt: str,
        content: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """Send content to Claude for analysis.

        Args:
            prompt: The analysis prompt/instructions
            content: The content to analyze
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0.0 = deterministic)

        Returns:
            Claude's response text

        Raises:
            ClaudeAPIError: If API call fails
        """
        full_prompt = f"{prompt}\n\n---\n\n{content}"

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are an expert sales analyst.",
                messages=[
                    {"role": "user", "content": full_prompt},
                ],
            )

            return message.content[0].text

        except RateLimitError as e:
            logger.error(f"Claude rate limit exceeded: {e}")
            raise ClaudeAPIError(f"Rate limit exceeded: {e}") from e
        except APIConnectionError as e:
            logger.error(f"Failed to connect to Claude API: {e}")
            raise ClaudeAPIError(f"Connection error: {e}") from e
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise ClaudeAPIError(f"API error: {e}") from e

    async def analyze_structured(
        self,
        prompt: str,
        content: str,
        response_model: type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> T:
        """Send content to Claude and parse response into a Pydantic model.

        Args:
            prompt: The analysis prompt/instructions
            content: The content to analyze
            response_model: Pydantic model class to parse response into
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Response temperature

        Returns:
            Parsed Pydantic model instance

        Raises:
            ClaudeAPIError: If API call fails
            ClaudeParseError: If response parsing fails
        """
        # Add JSON instruction to prompt
        json_schema = response_model.model_json_schema()
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"Respond with a valid JSON object matching this schema:\n"
            f"```json\n{json.dumps(json_schema, indent=2)}\n```\n\n"
            f"Output ONLY the JSON object, no additional text."
        )

        response = await self.analyze(
            prompt=enhanced_prompt,
            content=content,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return self._parse_json_response(response, response_model)

    def _parse_json_response(self, response: str, model: type[T]) -> T:
        """Parse a JSON response into a Pydantic model.

        Args:
            response: Raw response text from Claude
            model: Pydantic model class

        Returns:
            Parsed model instance

        Raises:
            ClaudeParseError: If parsing fails
        """
        # Clean up response - remove markdown code blocks if present
        cleaned = response.strip()

        if cleaned.startswith("```"):
            # Remove markdown code block
            lines = cleaned.split("\n")
            # Remove first line (```json or ```)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            return model.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            raise ClaudeParseError(f"Invalid JSON in response: {e}") from e
        except Exception as e:
            logger.error(f"Failed to validate response model: {e}\nData: {cleaned}")
            raise ClaudeParseError(f"Response validation failed: {e}") from e

    async def extract_json(
        self,
        prompt: str,
        content: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Extract a JSON object from content using Claude.

        Args:
            prompt: Extraction instructions
            content: Content to extract from
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Extracted JSON as a dictionary

        Raises:
            ClaudeAPIError: If API call fails
            ClaudeParseError: If JSON parsing fails
        """
        enhanced_prompt = (
            f"{prompt}\n\n"
            "Respond with ONLY a valid JSON object, no additional text or explanation."
        )

        response = await self.analyze(
            prompt=enhanced_prompt,
            content=content,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ClaudeParseError(f"Failed to parse JSON: {e}") from e


# Singleton instance
_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get the Claude client singleton.

    Returns:
        Configured ClaudeClient instance

    Raises:
        ClaudeClientError: If client cannot be initialized
    """
    global _client

    if _client is None:
        _client = ClaudeClient()

    return _client
