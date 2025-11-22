"""Sales OS API routes."""

from app.api.slack import router as slack_router
from app.api.webhooks import router as webhooks_router

__all__ = ["slack_router", "webhooks_router"]
