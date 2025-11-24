"""API route handlers."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.health import router as health_router

# Create main API router
api_router = APIRouter()

# Include core routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])

# Include transcript router
try:
    from app.api.transcript import router as transcript_router
    api_router.include_router(transcript_router, prefix="/transcript", tags=["Transcript"])
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to load transcript router: {e}")

# Try to include other routers if they exist
try:
    from app.api.webhooks import router as webhooks_router
    api_router.include_router(webhooks_router)
except ImportError:
    pass

try:
    from app.api.avoma import router as avoma_router
    api_router.include_router(avoma_router, prefix="/avoma", tags=["Avoma"])
except ImportError:
    pass

try:
    from app.api.zoom import router as zoom_router
    api_router.include_router(zoom_router, prefix="/zoom", tags=["Zoom"])
except ImportError:
    pass

try:
    from app.api.notifications import router as notifications_router
    api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
except ImportError:
    pass

try:
    from app.api.files import router as files_router
    api_router.include_router(files_router, prefix="/files", tags=["Files"])
except ImportError:
    pass

try:
    from app.api import activity
    api_router.include_router(activity.router, prefix="/activities", tags=["Activities"])
except ImportError:
    pass

try:
    from app.api.linkedin import router as linkedin_router
    api_router.include_router(linkedin_router, prefix="/linkedin", tags=["LinkedIn"])
except ImportError:
    pass

try:
    from app.api.slack import router as slack_router
    api_router.include_router(slack_router, prefix="/slack", tags=["Slack"])
except ImportError:
    pass

try:
    from app.api.battlecards import router as battlecards_router
    api_router.include_router(battlecards_router, prefix="/battlecards", tags=["Battlecards"])
except ImportError:
    pass

try:
    from app.api.dealroom import router as dealroom_router
    api_router.include_router(dealroom_router, prefix="/dealroom", tags=["DealRoom"])
except ImportError:
    pass

try:
    from app.api.enrichment import router as enrichment_router
    api_router.include_router(enrichment_router, prefix="/enrichment", tags=["Enrichment"])
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to load enrichment router: {e}")

try:
    from app.api.content import router as content_router
    api_router.include_router(content_router, tags=["Content"])  # Router already has /content prefix
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to load content router: {e}")

__all__ = ["api_router"]
