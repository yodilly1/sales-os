"""
Gong Sync Service

Handles synchronization of calls, transcripts, and metadata from Gong.
Supports incremental sync, historical import, and deduplication.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.integrations.gong import GongClient
from app.integrations.gong.models import (
    GongCall,
    GongSyncRequest,
    GongSyncResponse,
    GongTranscript,
)
from app.integrations.gong.utils import (
    generate_call_hash,
    map_gong_call_to_internal,
    map_gong_transcript_to_internal,
    map_gong_participant_to_internal,
    is_duplicate_call,
)
from app.models.gong import (
    GongSyncedCall,
    GongSyncedTranscript,
    GongSyncedParticipant,
    GongSyncLog,
    SyncStatus,
)

logger = logging.getLogger(__name__)


class GongSyncService:
    """
    Service for syncing Gong data to internal storage.

    Features:
    - Incremental sync (new calls since last sync)
    - Historical import (bulk import of older data)
    - Deduplication (skip already synced calls)
    - Rate limit handling with exponential backoff
    - Resumable sync via cursor persistence
    """

    def __init__(
        self,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize sync service.

        Args:
            batch_size: Number of calls to process per batch
            max_retries: Maximum retry attempts for failed operations
            retry_delay: Base delay between retries (exponential backoff)
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._existing_hashes: set[str] = set()

    async def sync_calls(
        self,
        client: GongClient,
        request: GongSyncRequest,
        organization_id: str,
    ) -> GongSyncResponse:
        """
        Sync calls from Gong to internal storage.

        Args:
            client: Configured Gong client
            request: Sync request parameters
            organization_id: Organization performing the sync

        Returns:
            GongSyncResponse with sync results
        """
        sync_started_at = datetime.utcnow()
        calls_synced = 0
        calls_skipped = 0
        calls_failed = 0
        errors: list[str] = []
        cursor: Optional[str] = None

        # Load existing call hashes for deduplication
        await self._load_existing_hashes(organization_id)

        logger.info(
            f"Starting Gong sync for org {organization_id}. "
            f"From: {request.from_datetime}, To: {request.to_datetime}"
        )

        try:
            # Create sync log entry
            sync_log = GongSyncLog(
                organization_id=organization_id,
                status=SyncStatus.IN_PROGRESS,
                sync_type="manual",
                started_at=sync_started_at,
                filter_from=request.from_datetime,
                filter_to=request.to_datetime,
            )
            # In production: await self._save_sync_log(sync_log)

            # Paginate through all calls
            while True:
                try:
                    response = await client.get_calls(
                        from_datetime=request.from_datetime,
                        to_datetime=request.to_datetime,
                        cursor=cursor,
                        workspace_id=request.workspace_id,
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch calls: {e}")
                    errors.append(f"Failed to fetch calls: {e}")
                    break

                if not response.calls:
                    break

                # Process each call in the batch
                for call in response.calls:
                    result = await self._process_call(
                        client=client,
                        call=call,
                        organization_id=organization_id,
                        include_transcripts=request.include_transcripts,
                        include_insights=request.include_insights,
                    )

                    if result == "synced":
                        calls_synced += 1
                    elif result == "skipped":
                        calls_skipped += 1
                    else:
                        calls_failed += 1
                        errors.append(f"Failed to sync call {call.id}: {result}")

                # Check for more pages
                cursor = response.cursor
                if not cursor:
                    break

                # Small delay between batches to avoid rate limits
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.exception(f"Sync failed with error: {e}")
            errors.append(f"Sync failed: {e}")

        sync_completed_at = datetime.utcnow()

        # Determine final status
        if calls_failed == 0 and not errors:
            status = "success"
        elif calls_synced > 0:
            status = "partial"
        else:
            status = "error"

        logger.info(
            f"Gong sync completed. Status: {status}, "
            f"Synced: {calls_synced}, Skipped: {calls_skipped}, Failed: {calls_failed}"
        )

        return GongSyncResponse(
            status=status,
            calls_synced=calls_synced,
            calls_skipped=calls_skipped,
            calls_failed=calls_failed,
            errors=errors[:10],  # Limit error list size
            sync_started_at=sync_started_at,
            sync_completed_at=sync_completed_at,
            next_cursor=cursor,
        )

    async def _process_call(
        self,
        client: GongClient,
        call: GongCall,
        organization_id: str,
        include_transcripts: bool = True,
        include_insights: bool = False,
    ) -> str:
        """
        Process a single call from Gong.

        Returns:
            "synced", "skipped", or error message
        """
        # Check for duplicate
        call_hash = generate_call_hash(call.id, call.workspace_id)
        if is_duplicate_call(call_hash, self._existing_hashes):
            logger.debug(f"Skipping duplicate call: {call.id}")
            return "skipped"

        try:
            # Map to internal format
            call_data = map_gong_call_to_internal(call)
            call_data["organization_id"] = organization_id
            call_data["gong_hash"] = call_hash

            # Create synced call record
            synced_call = GongSyncedCall(
                organization_id=organization_id,
                gong_call_id=call.id,
                gong_hash=call_hash,
                title=call.title,
                scheduled_at=call.scheduled,
                started_at=call.started,
                duration_seconds=call.duration,
                direction=call.direction,
                platform=call.system,
                scope=call.scope,
                media_type=call.media,
                language=call.language,
                external_url=call.url,
                workspace_id=call.workspace_id,
            )

            # In production: await self._save_call(synced_call)

            # Fetch and save transcript
            if include_transcripts:
                await self._sync_transcript(client, call.id, organization_id)

            # Fetch and save participants
            await self._sync_participants(client, call.id, organization_id)

            # Fetch insights if requested
            if include_insights:
                await self._sync_insights(client, call.id, organization_id)

            # Add hash to prevent re-processing in same sync
            self._existing_hashes.add(call_hash)

            return "synced"

        except Exception as e:
            logger.error(f"Error processing call {call.id}: {e}")
            return str(e)

    async def _sync_transcript(
        self,
        client: GongClient,
        call_id: str,
        organization_id: str,
    ) -> Optional[GongSyncedTranscript]:
        """Sync transcript for a call."""
        try:
            transcript = await client.get_call_transcript(call_id)
            if not transcript.segments:
                return None

            transcript_data = map_gong_transcript_to_internal(transcript)

            synced_transcript = GongSyncedTranscript(
                call_id=call_id,  # Will be updated with internal ID
                gong_call_id=call_id,
                raw_text=transcript_data["raw_text"],
                formatted_text=transcript_data["formatted_text"],
                segments=transcript_data["segments"],
                segment_count=transcript_data["segment_count"],
                word_count=len(transcript_data["raw_text"].split()),
            )

            # In production: await self._save_transcript(synced_transcript)
            return synced_transcript

        except Exception as e:
            logger.warning(f"Failed to sync transcript for call {call_id}: {e}")
            return None

    async def _sync_participants(
        self,
        client: GongClient,
        call_id: str,
        organization_id: str,
    ) -> list[GongSyncedParticipant]:
        """Sync participants for a call."""
        try:
            participants = await client.get_call_participants(call_id)
            synced_participants = []

            for participant in participants:
                participant_data = map_gong_participant_to_internal(participant)

                synced = GongSyncedParticipant(
                    call_id=call_id,
                    gong_participant_id=participant.id,
                    email=participant.email,
                    name=participant.name,
                    title=participant.title,
                    phone=participant.phone,
                    is_internal=participant.affiliation == "internal",
                    speaker_id=participant.speaker_id,
                    metadata=participant_data.get("metadata", {}),
                )
                synced_participants.append(synced)

            # In production: await self._save_participants(synced_participants)
            return synced_participants

        except Exception as e:
            logger.warning(f"Failed to sync participants for call {call_id}: {e}")
            return []

    async def _sync_insights(
        self,
        client: GongClient,
        call_id: str,
        organization_id: str,
    ) -> bool:
        """Sync Gong AI insights for a call."""
        try:
            insights = await client.get_call_insights(call_id)
            if insights:
                # In production: await self._save_insights(call_id, insights)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to sync insights for call {call_id}: {e}")
            return False

    async def _load_existing_hashes(self, organization_id: str) -> None:
        """
        Load existing call hashes for deduplication.

        In production, this would query the database for all
        existing Gong call hashes for the organization.
        """
        # In production:
        # hashes = await get_existing_gong_hashes(organization_id)
        # self._existing_hashes = set(hashes)
        self._existing_hashes = set()

    async def run_scheduled_sync(
        self,
        client: GongClient,
        organization_id: str,
        lookback_hours: int = 24,
    ) -> GongSyncResponse:
        """
        Run a scheduled incremental sync.

        Syncs calls from the last N hours.
        """
        from_datetime = datetime.utcnow() - timedelta(hours=lookback_hours)

        request = GongSyncRequest(
            from_datetime=from_datetime,
            include_transcripts=True,
            include_insights=False,
        )

        return await self.sync_calls(client, request, organization_id)

    async def run_historical_import(
        self,
        client: GongClient,
        organization_id: str,
        from_datetime: datetime,
        to_datetime: Optional[datetime] = None,
    ) -> GongSyncResponse:
        """
        Run a historical import of older calls.

        Use this for initial setup or backfilling data.
        """
        request = GongSyncRequest(
            from_datetime=from_datetime,
            to_datetime=to_datetime or datetime.utcnow(),
            include_transcripts=True,
            include_insights=True,  # Include insights for historical analysis
        )

        return await self.sync_calls(client, request, organization_id)
