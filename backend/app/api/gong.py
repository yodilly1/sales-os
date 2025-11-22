"""
Gong API Routes

FastAPI routes for Gong integration management, call retrieval,
and sync operations.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel

from app.integrations.gong import GongClient
from app.integrations.gong.models import GongSyncRequest, GongSyncResponse
from app.models.gong import (
    GongConnectRequest,
    GongConnectResponse,
    GongStatusResponse,
    GongCallListRequest,
    GongCallListResponse,
    GongCallResponse,
    GongSyncTriggerRequest,
    GongSyncStatusResponse,
    GongSyncLog,
    IntegrationStatus,
    SyncStatus,
)
from app.services.gong.sync_service import GongSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gong", tags=["gong"])


# Placeholder for dependency injection - in production, this would
# come from a proper DI system with database sessions
async def get_gong_client() -> Optional[GongClient]:
    """
    Get configured Gong client for the current organization.

    In production, this would:
    1. Get the current user/org from auth context
    2. Fetch their stored Gong credentials from DB
    3. Decrypt and return a configured client
    """
    # Placeholder - would be replaced with actual credential retrieval
    return None


async def get_sync_service() -> GongSyncService:
    """Get Gong sync service instance."""
    return GongSyncService()


# ==============================================================================
# Authentication & Connection Endpoints
# ==============================================================================


@router.post("/connect", response_model=GongConnectResponse)
async def connect_gong(request: GongConnectRequest):
    """
    Connect Gong integration with API credentials.

    This endpoint:
    1. Validates the provided credentials against Gong API
    2. Stores encrypted credentials for the organization
    3. Initiates an initial sync of recent calls
    """
    client = GongClient(
        access_key=request.access_key,
        access_key_secret=request.access_key_secret,
    )

    try:
        # Verify credentials are valid
        await client.verify_credentials()

        # In production: encrypt and store credentials in database
        # await store_gong_credentials(org_id, request)

        logger.info("Gong integration connected successfully")

        return GongConnectResponse(
            status=IntegrationStatus.CONNECTED,
            message="Gong integration connected successfully",
            connected_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to connect Gong: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to Gong: {str(e)}",
        )
    finally:
        await client.close()


@router.post("/disconnect")
async def disconnect_gong():
    """
    Disconnect Gong integration.

    This removes stored credentials but preserves synced data.
    """
    # In production: remove stored credentials from database
    # await delete_gong_credentials(org_id)

    logger.info("Gong integration disconnected")

    return {
        "status": "success",
        "message": "Gong integration disconnected",
    }


@router.get("/status", response_model=GongStatusResponse)
async def get_gong_status():
    """
    Get current Gong integration status.

    Returns connection status, last sync time, and statistics.
    """
    # In production: fetch from database
    # config = await get_gong_config(org_id)
    # if not config:
    #     return GongStatusResponse(status=IntegrationStatus.DISCONNECTED)

    # Placeholder response
    return GongStatusResponse(
        status=IntegrationStatus.DISCONNECTED,
        workspace_id=None,
        last_sync_at=None,
        total_calls_synced=0,
        last_error=None,
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Gong integration.

    Tests connectivity to Gong API if configured.
    """
    client = await get_gong_client()
    if not client:
        return {
            "status": "not_configured",
            "message": "Gong integration is not configured",
        }

    try:
        await client.verify_credentials()
        return {
            "status": "healthy",
            "message": "Gong API connection is healthy",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
        }
    finally:
        await client.close()


# ==============================================================================
# Call Retrieval Endpoints
# ==============================================================================


@router.get("/calls", response_model=GongCallListResponse)
async def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: Optional[str] = None,
):
    """
    List synced Gong calls.

    Returns paginated list of calls that have been synced from Gong.
    """
    # In production: query database for synced calls
    # calls = await get_synced_calls(org_id, page, page_size, from_date, to_date, search)

    # Placeholder response
    return GongCallListResponse(
        calls=[],
        total=0,
        page=page,
        page_size=page_size,
        has_more=False,
    )


@router.get("/calls/{call_id}", response_model=GongCallResponse)
async def get_call(call_id: str):
    """
    Get details for a specific synced call.

    Includes participants and transcript availability.
    """
    # In production: fetch from database
    # call = await get_synced_call(org_id, call_id)
    # if not call:
    #     raise HTTPException(status_code=404, detail="Call not found")

    raise HTTPException(status_code=404, detail="Call not found")


@router.get("/calls/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    """
    Get the transcript for a specific call.

    Returns the full transcript with speaker information and timestamps.
    """
    # In production: fetch from database
    # transcript = await get_call_transcript(org_id, call_id)
    # if not transcript:
    #     raise HTTPException(status_code=404, detail="Transcript not found")

    raise HTTPException(status_code=404, detail="Transcript not found")


@router.get("/calls/{call_id}/participants")
async def get_call_participants(call_id: str):
    """
    Get participants for a specific call.
    """
    # In production: fetch from database
    raise HTTPException(status_code=404, detail="Call not found")


@router.post("/calls/{call_id}/process")
async def process_call(call_id: str, background_tasks: BackgroundTasks):
    """
    Trigger processing/analysis for a specific call.

    This can include:
    - SPICED framework analysis
    - Key moment extraction
    - Action item detection
    """
    # In production: queue background job
    # background_tasks.add_task(process_call_async, org_id, call_id)

    return {
        "status": "queued",
        "message": f"Call {call_id} queued for processing",
    }


# ==============================================================================
# Sync Endpoints
# ==============================================================================


@router.post("/sync", response_model=GongSyncResponse)
async def trigger_sync(
    request: GongSyncTriggerRequest,
    background_tasks: BackgroundTasks,
    sync_service: GongSyncService = Depends(get_sync_service),
):
    """
    Trigger a sync operation to import calls from Gong.

    Sync types:
    - incremental: Sync new calls since last sync
    - full: Re-sync all calls within date range
    - historical: Import older historical data
    """
    client = await get_gong_client()
    if not client:
        raise HTTPException(
            status_code=400,
            detail="Gong integration is not configured",
        )

    # Start sync in background
    sync_request = GongSyncRequest(
        from_datetime=request.from_datetime,
        to_datetime=request.to_datetime,
        include_transcripts=request.include_transcripts,
        include_insights=request.include_insights,
    )

    # In production: run async
    # background_tasks.add_task(sync_service.sync_calls, client, sync_request)

    return GongSyncResponse(
        status="queued",
        calls_synced=0,
        calls_skipped=0,
        calls_failed=0,
        sync_started_at=datetime.utcnow(),
    )


@router.get("/sync/status", response_model=GongSyncStatusResponse)
async def get_sync_status():
    """
    Get current sync status.

    Returns whether a sync is in progress and details of the last sync.
    """
    # In production: check sync status from database/cache
    return GongSyncStatusResponse(
        is_syncing=False,
        last_sync=None,
        next_scheduled_sync=None,
    )


@router.get("/sync/history")
async def get_sync_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get history of sync operations.
    """
    # In production: fetch sync logs from database
    return {
        "syncs": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


# ==============================================================================
# Webhook Endpoint (if Gong sends webhooks)
# ==============================================================================


class GongWebhookEvent(BaseModel):
    """Gong webhook event payload."""

    event_type: str
    call_id: Optional[str] = None
    data: dict = {}


@router.post("/webhook")
async def handle_webhook(event: GongWebhookEvent, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from Gong.

    Gong can send webhooks for:
    - New call completed
    - Transcript ready
    - Call deleted
    """
    logger.info(f"Received Gong webhook: {event.event_type}")

    # In production: validate webhook signature and process
    # if event.event_type == "call.completed":
    #     background_tasks.add_task(sync_single_call, event.call_id)

    return {"status": "received"}


# ==============================================================================
# Direct API Proxy (for advanced use cases)
# ==============================================================================


@router.get("/proxy/calls")
async def proxy_list_calls(
    from_datetime: Optional[datetime] = None,
    to_datetime: Optional[datetime] = None,
    cursor: Optional[str] = None,
):
    """
    Proxy endpoint to directly fetch calls from Gong API.

    Useful for previewing data before sync or debugging.
    """
    client = await get_gong_client()
    if not client:
        raise HTTPException(
            status_code=400,
            detail="Gong integration is not configured",
        )

    try:
        response = await client.get_calls(
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            cursor=cursor,
        )

        return {
            "calls": [call.model_dump() for call in response.calls],
            "cursor": response.cursor,
            "total_records": response.total_records,
        }
    finally:
        await client.close()
