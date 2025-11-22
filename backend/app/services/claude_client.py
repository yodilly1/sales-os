"""
Claude API Client Service

Provides a unified interface for interacting with Claude AI using
the Sales OS prompt templates.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Optional

# Add claude module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from claude.lib.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class ClaudeModel(Enum):
    """Available Claude models."""
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"


@dataclass
class ClaudeConfig:
    """Configuration for Claude API client."""
    api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: ClaudeModel = ClaudeModel.CLAUDE_3_5_SONNET
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: float = 120.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    def __post_init__(self):
        if not self.api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not set. Claude API calls will fail."
            )


@dataclass
class ClaudeResponse:
    """Response from Claude API."""
    content: str
    model: str
    usage: dict[str, int]
    stop_reason: str
    prompt_name: Optional[str] = None
    prompt_version: Optional[str] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def parsed_json(self) -> Optional[dict]:
        """Attempt to parse response content as JSON."""
        try:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", self.content)
            if json_match:
                return json.loads(json_match.group(1).strip())
            # Try raw JSON
            return json.loads(self.content)
        except (json.JSONDecodeError, AttributeError):
            return None

    def to_dict(self) -> dict:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "stop_reason": self.stop_reason,
            "prompt_name": self.prompt_name,
            "prompt_version": self.prompt_version,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
        }


class ClaudeClientError(Exception):
    """Base exception for Claude client errors."""
    pass


class ClaudeAPIError(ClaudeClientError):
    """Raised when Claude API returns an error."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ClaudeRateLimitError(ClaudeClientError):
    """Raised when rate limited by Claude API."""
    def __init__(self, retry_after: Optional[float] = None):
        super().__init__("Rate limited by Claude API")
        self.retry_after = retry_after


class ClaudeClient:
    """
    Client for interacting with Claude AI API.

    Integrates with the Sales OS prompt management system to provide
    a unified interface for AI-powered features.

    Usage:
        client = ClaudeClient()

        # Using a prompt template
        response = await client.run_prompt(
            "spiced_extraction",
            variables={"transcript": "..."}
        )

        # Direct message (without template)
        response = await client.send_message(
            "Analyze this text...",
            system="You are a helpful assistant."
        )

    Features:
        - Prompt template integration
        - Automatic retry with exponential backoff
        - Response parsing and validation
        - Usage tracking and logging
        - Streaming support
    """

    def __init__(
        self,
        config: Optional[ClaudeConfig] = None,
        prompt_manager: Optional[PromptManager] = None
    ):
        """
        Initialize the Claude client.

        Args:
            config: Configuration options
            prompt_manager: Prompt manager instance (creates default if None)
        """
        self.config = config or ClaudeConfig()
        self._prompt_manager = prompt_manager or PromptManager()
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Anthropic client."""
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.config.api_key)
            self._async_client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
        except ImportError:
            logger.warning(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )
            self._client = None
            self._async_client = None

    @property
    def prompt_manager(self) -> PromptManager:
        """Get the prompt manager instance."""
        return self._prompt_manager

    def list_prompts(self) -> list[str]:
        """List all available prompt templates."""
        return self._prompt_manager.list_prompts()

    def get_prompt_info(self, name: str) -> dict:
        """Get information about a prompt template."""
        metadata = self._prompt_manager.get_metadata(name)
        validation = self._prompt_manager.validate_prompt(name)
        return {
            "name": metadata.name,
            "version": metadata.version,
            "category": metadata.category,
            "valid": validation["valid"],
            "required_variables": validation.get("variables_required", []),
        }

    async def run_prompt(
        self,
        prompt_name: str,
        variables: Optional[dict[str, Any]] = None,
        model: Optional[ClaudeModel] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ClaudeResponse:
        """
        Run a prompt template with variables.

        Args:
            prompt_name: Name of the prompt template
            variables: Variables to substitute in template
            model: Model to use (overrides config)
            max_tokens: Max tokens (overrides config)
            temperature: Temperature (overrides config)

        Returns:
            ClaudeResponse with the model's output

        Raises:
            ClaudeClientError: If prompt or API call fails
        """
        # Get the prompt with variables substituted
        prompt = self._prompt_manager.get_prompt(prompt_name, variables or {})

        response = await self.send_message(
            user_message=prompt["user"],
            system=prompt["system"],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Add prompt metadata to response
        response.prompt_name = prompt_name
        response.prompt_version = prompt["version"]

        return response

    async def send_message(
        self,
        user_message: str,
        system: Optional[str] = None,
        model: Optional[ClaudeModel] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ClaudeResponse:
        """
        Send a message to Claude.

        Args:
            user_message: The user's message
            system: System prompt
            model: Model to use
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            ClaudeResponse with the model's output
        """
        import time

        if not self._async_client:
            raise ClaudeClientError(
                "Anthropic client not initialized. "
                "Ensure anthropic package is installed and API key is set."
            )

        model = model or self.config.model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature if temperature is not None else self.config.temperature

        start_time = time.time()

        # Build request
        request_params = {
            "model": model.value,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_message}],
        }

        if system:
            request_params["system"] = system

        # Execute with retry
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._async_client.messages.create(**request_params)
                latency_ms = (time.time() - start_time) * 1000

                return ClaudeResponse(
                    content=response.content[0].text if response.content else "",
                    model=response.model,
                    usage={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    stop_reason=response.stop_reason,
                    latency_ms=latency_ms,
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Claude API attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt < self.config.retry_attempts - 1:
                    import asyncio
                    delay = self.config.retry_delay_seconds * (2 ** attempt)
                    await asyncio.sleep(delay)

        raise ClaudeAPIError(f"API call failed after {self.config.retry_attempts} attempts: {last_error}")

    async def stream_message(
        self,
        user_message: str,
        system: Optional[str] = None,
        model: Optional[ClaudeModel] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """
        Stream a response from Claude.

        Args:
            user_message: The user's message
            system: System prompt
            model: Model to use
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Yields:
            Text chunks as they are generated
        """
        if not self._async_client:
            raise ClaudeClientError("Anthropic client not initialized.")

        model = model or self.config.model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature if temperature is not None else self.config.temperature

        request_params = {
            "model": model.value,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_message}],
        }

        if system:
            request_params["system"] = system

        async with self._async_client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text

    def run_prompt_sync(
        self,
        prompt_name: str,
        variables: Optional[dict[str, Any]] = None,
        model: Optional[ClaudeModel] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ClaudeResponse:
        """
        Synchronous version of run_prompt.

        Args:
            prompt_name: Name of the prompt template
            variables: Variables to substitute
            model: Model override
            max_tokens: Max tokens override
            temperature: Temperature override

        Returns:
            ClaudeResponse
        """
        import time

        if not self._client:
            raise ClaudeClientError("Anthropic client not initialized.")

        prompt = self._prompt_manager.get_prompt(prompt_name, variables or {})

        model = model or self.config.model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature if temperature is not None else self.config.temperature

        start_time = time.time()

        request_params = {
            "model": model.value,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt["user"]}],
        }

        if prompt.get("system"):
            request_params["system"] = prompt["system"]

        response = self._client.messages.create(**request_params)
        latency_ms = (time.time() - start_time) * 1000

        return ClaudeResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            stop_reason=response.stop_reason,
            prompt_name=prompt_name,
            prompt_version=prompt["version"],
            latency_ms=latency_ms,
        )

    # Convenience methods for specific prompts

    async def extract_spiced(
        self,
        transcript: str,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        call_date: Optional[str] = None,
        call_type: str = "discovery",
    ) -> ClaudeResponse:
        """
        Extract SPICED elements from a transcript.

        Args:
            transcript: Call transcript text
            company_name: Optional company name
            contact_name: Optional contact name
            call_date: Optional call date
            call_type: Type of call (discovery, demo, etc.)

        Returns:
            ClaudeResponse with SPICED extraction
        """
        return await self.run_prompt(
            "spiced_extraction",
            variables={
                "transcript": transcript,
                "company_name": company_name or "",
                "contact_name": contact_name or "",
                "call_date": call_date or datetime.now().strftime("%Y-%m-%d"),
                "call_type": call_type,
            }
        )

    async def generate_coaching(
        self,
        content: str,
        rep_name: str,
        call_type: str = "discovery",
        deal_stage: str = "qualification",
    ) -> ClaudeResponse:
        """
        Generate coaching feedback for a sales call.

        Args:
            content: Call transcript or SPICED extraction
            rep_name: Sales rep name
            call_type: Type of call
            deal_stage: Current deal stage

        Returns:
            ClaudeResponse with coaching feedback
        """
        return await self.run_prompt(
            "spiced_coaching",
            variables={
                "content": content,
                "rep_name": rep_name,
                "call_type": call_type,
                "call_date": datetime.now().strftime("%Y-%m-%d"),
                "deal_stage": deal_stage,
            }
        )

    async def enrich_prospect(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        product_description: Optional[str] = None,
    ) -> ClaudeResponse:
        """
        Enrich prospect data.

        Args:
            name: Prospect name
            email: Email address
            company: Company name
            title: Job title
            linkedin_url: LinkedIn profile URL
            product_description: Description of our product

        Returns:
            ClaudeResponse with enriched data
        """
        return await self.run_prompt(
            "prospect_enrichment",
            variables={
                "name": name,
                "email": email or "",
                "company": company or "",
                "title": title or "",
                "linkedin_url": linkedin_url or "",
                "product_description": product_description or "Sales automation platform",
            }
        )


# Factory function for easy instantiation
def create_claude_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> ClaudeClient:
    """
    Create a configured Claude client.

    Args:
        api_key: API key (defaults to ANTHROPIC_API_KEY env var)
        model: Model name (defaults to claude-3-5-sonnet)

    Returns:
        Configured ClaudeClient instance
    """
    config = ClaudeConfig(
        api_key=api_key or os.getenv("ANTHROPIC_API_KEY", ""),
        model=ClaudeModel(model) if model else ClaudeModel.CLAUDE_3_5_SONNET,
    )
    return ClaudeClient(config=config)
