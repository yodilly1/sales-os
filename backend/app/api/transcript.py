"""Transcript parsing and SPICED extraction API routes."""
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.models.transcript import (
    CallNote,
    FollowUpTask,
    TranscriptParseRequest,
    TranscriptParseResponse,
    TranscriptData,
    TaskPriority,
)
from app.models.spiced import SPICEDAnalysis
from app.services.claude_client import ClaudeClientError
from app.services.transcript.parser import TranscriptParser
from app.services.transcript.spiced_extractor import SPICEDExtractor

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== In-Memory Storage ====================
# Simple in-memory storage for MVP - stores transcripts between requests
# In production, this would be replaced with database persistence

class StoredTranscript(BaseModel):
    """A stored transcript with all its associated data."""
    id: str
    title: str
    source: str = "manual"
    status: str = "completed"
    duration: int = 0
    participant_count: int = 0
    created_at: str
    raw_text: str
    transcript_data: Dict[str, Any]
    spiced_analysis: Optional[Dict[str, Any]] = None
    call_note: Optional[Dict[str, Any]] = None
    tasks: List[Dict[str, Any]] = []
    notes_content: Optional[str] = None
    crm_status: str = "not_synced"
    crm_record_id: Optional[str] = None
    overall_score: Optional[float] = None


class TranscriptListItem(BaseModel):
    """Summary item for transcript list."""
    id: str
    title: str
    source: str
    duration: int
    participantCount: int
    status: str
    crmStatus: str
    createdAt: str
    overallScore: Optional[float] = None


class TranscriptListResponse(BaseModel):
    """Paginated list of transcripts."""
    data: List[TranscriptListItem]
    total: int
    page: int
    pageSize: int


class NotesUpdateRequest(BaseModel):
    """Request to update notes."""
    content: str


class TaskToggleRequest(BaseModel):
    """Request to toggle task completion."""
    completed: bool


class StoredTask(BaseModel):
    """A task with completion status."""
    id: str
    title: str
    description: str
    priority: str = "medium"
    completed: bool = False
    due_date_suggestion: Optional[str] = None
    related_spiced_component: Optional[str] = None


# In-memory storage
_transcript_store: Dict[str, StoredTranscript] = {}


def _calculate_overall_score(spiced: Dict[str, Any]) -> Optional[float]:
    """Calculate overall SPICED score from individual component scores."""
    scores = []
    for component in ['situation', 'pain', 'impact', 'critical_event', 'decision_process', 'decision_criteria']:
        if component in spiced and isinstance(spiced[component], dict):
            score = spiced[component].get('score')
            if score is not None:
                scores.append(score)
    if scores:
        return sum(scores) / len(scores)
    return None


@router.post(
    "/parse",
    response_model=TranscriptParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse transcript and extract SPICED analysis",
    description="""
    Parse a raw sales call transcript and extract SPICED methodology information.

    This endpoint:
    1. Parses the transcript into structured turns
    2. Identifies speakers and their roles
    3. Extracts SPICED analysis using Claude AI
    4. Generates formatted call notes (optional)
    5. Suggests follow-up tasks (optional)

    Supports transcripts from various platforms:
    - Zoom
    - Microsoft Teams
    - Avoma
    - Gong
    - Chorus
    - Generic/plain text

    The SPICED analysis includes:
    - **S**ituation: Current state and context
    - **P**ain: Problems and challenges
    - **I**mpact: Business consequences
    - **C**ritical Event: Timeline and urgency
    - **E**xpected Decision: Decision process
    - **D**ecision Criteria: Evaluation criteria
    """,
    responses={
        200: {
            "description": "Transcript parsed and analyzed successfully",
        },
        400: {
            "description": "Invalid transcript format or content",
        },
        500: {
            "description": "Internal server error during analysis",
        },
        503: {
            "description": "Claude API unavailable or rate limited",
        },
    },
)
async def parse_transcript(
    request: TranscriptParseRequest,
) -> TranscriptParseResponse:
    """Parse a transcript and extract SPICED analysis.

    Args:
        request: Transcript parse request with raw text and options

    Returns:
        TranscriptParseResponse with parsed transcript, SPICED analysis,
        call notes, and follow-up tasks

    Raises:
        HTTPException: If parsing or analysis fails
    """
    start_time = time.time()
    warnings: list[str] = []

    try:
        # Parse the transcript
        parser = TranscriptParser(sales_rep_name=request.sales_rep_name)
        transcript = parser.parse(
            raw_text=request.transcript_text,
            format_hint=request.format,
            title=request.call_title,
            call_date=request.call_date,
        )

        # Warn if no turns were parsed
        if not transcript.turns:
            warnings.append(
                "Could not parse individual conversation turns. "
                "Analysis will use raw text."
            )

        # Extract SPICED analysis
        extractor = SPICEDExtractor()
        spiced_analysis = await extractor.extract(
            transcript=transcript,
            company_name=request.company_name,
        )

        # Generate optional outputs
        call_note: Optional[CallNote] = None
        follow_up_tasks: list[FollowUpTask] = []

        if request.generate_call_note:
            call_note = await extractor.generate_call_note(
                transcript=transcript,
                spiced=spiced_analysis,
            )

        if request.generate_tasks:
            follow_up_tasks = await extractor.generate_follow_up_tasks(
                spiced=spiced_analysis,
                company_name=request.company_name,
            )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Store the transcript in memory for later retrieval
        stored_tasks = []
        for i, task in enumerate(follow_up_tasks):
            stored_tasks.append({
                "id": str(uuid4()),
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "completed": False,
                "due_date_suggestion": task.due_date_suggestion,
                "related_spiced_component": task.related_spiced_component,
            })

        spiced_dict = spiced_analysis.model_dump() if hasattr(spiced_analysis, 'model_dump') else spiced_analysis.dict()
        overall_score = _calculate_overall_score(spiced_dict)

        stored = StoredTranscript(
            id=transcript.id,
            title=transcript.title or request.call_title or "Untitled Call",
            source="manual",
            status="completed",
            duration=(transcript.duration_minutes or 0) * 60,
            participant_count=len(transcript.speakers),
            created_at=transcript.created_at.isoformat() if transcript.created_at else datetime.utcnow().isoformat(),
            raw_text=transcript.raw_text,
            transcript_data=transcript.model_dump() if hasattr(transcript, 'model_dump') else transcript.dict(),
            spiced_analysis=spiced_dict,
            call_note=call_note.model_dump() if call_note and hasattr(call_note, 'model_dump') else (call_note.dict() if call_note else None),
            tasks=stored_tasks,
            notes_content=call_note.formatted_note if call_note else None,
            overall_score=overall_score,
        )
        _transcript_store[transcript.id] = stored
        logger.info(f"Stored transcript {transcript.id} in memory. Total stored: {len(_transcript_store)}")

        return TranscriptParseResponse(
            transcript=transcript,
            spiced_analysis=spiced_analysis,
            call_note=call_note,
            follow_up_tasks=follow_up_tasks,
            processing_time_ms=processing_time_ms,
            warnings=warnings,
        )

    except ClaudeClientError as e:
        logger.error(f"Claude API error during transcript analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI analysis service unavailable: {str(e)}",
        )
    except ValueError as e:
        logger.error(f"Invalid transcript format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transcript format: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Unexpected error during transcript analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transcript analysis",
        )


@router.post(
    "/analyze-spiced",
    response_model=SPICEDAnalysis,
    status_code=status.HTTP_200_OK,
    summary="Extract SPICED analysis only",
    description="""
    Extract only the SPICED analysis from a transcript, without call notes
    or task generation. Use this for faster analysis when you only need
    the SPICED breakdown.
    """,
)
async def analyze_spiced(
    request: TranscriptParseRequest,
) -> SPICEDAnalysis:
    """Extract SPICED analysis from a transcript.

    Args:
        request: Transcript with text and metadata

    Returns:
        SPICEDAnalysis with extracted information

    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Parse the transcript
        parser = TranscriptParser(sales_rep_name=request.sales_rep_name)
        transcript = parser.parse(
            raw_text=request.transcript_text,
            format_hint=request.format,
            title=request.call_title,
            call_date=request.call_date,
        )

        # Extract SPICED analysis
        extractor = SPICEDExtractor()
        return await extractor.extract(
            transcript=transcript,
            company_name=request.company_name,
        )

    except ClaudeClientError as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI analysis service unavailable: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Error during SPICED analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.post(
    "/generate-tasks",
    response_model=list[FollowUpTask],
    status_code=status.HTTP_200_OK,
    summary="Generate follow-up tasks from SPICED analysis",
    description="""
    Generate CRM-ready follow-up task recommendations from an existing
    SPICED analysis. Useful when you want to regenerate tasks or create
    tasks from a previously stored analysis.
    """,
)
async def generate_tasks(
    spiced_analysis: SPICEDAnalysis,
    company_name: Optional[str] = None,
) -> list[FollowUpTask]:
    """Generate follow-up tasks from SPICED analysis.

    Args:
        spiced_analysis: Existing SPICED analysis
        company_name: Optional company name for task titles

    Returns:
        List of recommended follow-up tasks
    """
    extractor = SPICEDExtractor()
    return await extractor.generate_follow_up_tasks(
        spiced=spiced_analysis,
        company_name=company_name,
    )


# ==================== CRUD Endpoints ====================

@router.get(
    "/",
    response_model=TranscriptListResponse,
    summary="List all transcripts",
    description="Get a paginated list of all stored transcripts.",
)
async def list_transcripts(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sortField: Optional[str] = "createdAt",
    sortDirection: Optional[str] = "desc",
) -> TranscriptListResponse:
    """List all stored transcripts with pagination."""
    transcripts = list(_transcript_store.values())

    # Search filter
    if search:
        search_lower = search.lower()
        transcripts = [t for t in transcripts if search_lower in t.title.lower()]

    # Sort
    reverse = sortDirection == "desc"
    if sortField == "createdAt":
        transcripts.sort(key=lambda t: t.created_at, reverse=reverse)
    elif sortField == "title":
        transcripts.sort(key=lambda t: t.title.lower(), reverse=reverse)

    # Paginate
    total = len(transcripts)
    start = (page - 1) * pageSize
    end = start + pageSize
    paginated = transcripts[start:end]

    # Convert to list items
    items = [
        TranscriptListItem(
            id=t.id,
            title=t.title,
            source=t.source,
            duration=t.duration,
            participantCount=t.participant_count,
            status=t.status,
            crmStatus=t.crm_status,
            createdAt=t.created_at,
            overallScore=t.overall_score,
        )
        for t in paginated
    ]

    return TranscriptListResponse(
        data=items,
        total=total,
        page=page,
        pageSize=pageSize,
    )


@router.get(
    "/{transcript_id}",
    summary="Get transcript by ID",
    description="Get a single transcript with all its data.",
)
async def get_transcript(transcript_id: str) -> Dict[str, Any]:
    """Get a transcript by ID."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    stored = _transcript_store[transcript_id]

    # Build response matching frontend Transcript type
    return {
        "id": stored.id,
        "title": stored.title,
        "source": stored.source,
        "status": stored.status,
        "duration": stored.duration,
        "participants": stored.transcript_data.get("speakers", []),
        "createdAt": stored.created_at,
        "rawText": stored.raw_text,
        "spicedAnalysis": _build_spiced_response(stored.spiced_analysis) if stored.spiced_analysis else None,
        "callNotes": {
            "id": f"notes-{stored.id}",
            "transcriptId": stored.id,
            "content": stored.notes_content or "",
            "autoGenerated": stored.call_note is not None,
            "editedAt": stored.created_at,
        } if stored.notes_content or stored.call_note else None,
        "crmStatus": stored.crm_status,
        "crmRecordId": stored.crm_record_id,
    }


def _build_spiced_response(spiced: Dict[str, Any]) -> Dict[str, Any]:
    """Build SPICED response matching frontend type."""
    elements = []
    for key in ['situation', 'pain', 'impact', 'critical_event', 'decision_process', 'decision_criteria']:
        if key in spiced and isinstance(spiced[key], dict):
            elem = spiced[key]
            elements.append({
                "key": key,
                "label": key.replace('_', ' ').title(),
                "score": elem.get('score', 0),
                "summary": elem.get('summary', ''),
                "details": elem.get('details', ''),
                "quotes": elem.get('quotes', []),
                "gaps": elem.get('gaps', []),
                "suggestedQuestions": elem.get('suggested_questions', []),
            })

    # Calculate overall score
    scores = [e['score'] for e in elements if e.get('score')]
    overall_score = sum(scores) / len(scores) if scores else 0

    return {
        "overallScore": overall_score,
        "elements": elements,
        "suggestedTasks": _transcript_store.get(spiced.get('transcript_id', ''), StoredTranscript(
            id='', title='', created_at='', raw_text='', transcript_data={}
        )).tasks if 'transcript_id' in spiced else [],
        "summary": spiced.get('summary', ''),
    }


@router.delete(
    "/{transcript_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transcript",
    description="Delete a transcript by ID.",
)
async def delete_transcript(transcript_id: str):
    """Delete a transcript."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    del _transcript_store[transcript_id]
    logger.info(f"Deleted transcript {transcript_id}. Remaining: {len(_transcript_store)}")


@router.put(
    "/{transcript_id}/notes",
    summary="Update call notes",
    description="Update the notes for a transcript.",
)
async def update_notes(transcript_id: str, request: NotesUpdateRequest) -> Dict[str, Any]:
    """Update notes for a transcript."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    stored = _transcript_store[transcript_id]
    stored.notes_content = request.content

    return {
        "id": f"notes-{transcript_id}",
        "transcriptId": transcript_id,
        "content": request.content,
        "autoGenerated": False,
        "editedAt": datetime.utcnow().isoformat(),
    }


@router.get(
    "/{transcript_id}/tasks",
    summary="Get tasks for transcript",
    description="Get all follow-up tasks for a transcript.",
)
async def get_tasks(transcript_id: str) -> List[Dict[str, Any]]:
    """Get tasks for a transcript."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    return _transcript_store[transcript_id].tasks


@router.patch(
    "/{transcript_id}/tasks/{task_id}",
    summary="Toggle task completion",
    description="Update the completion status of a task.",
)
async def toggle_task(
    transcript_id: str,
    task_id: str,
    request: TaskToggleRequest,
) -> Dict[str, Any]:
    """Toggle task completion status."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    stored = _transcript_store[transcript_id]

    for task in stored.tasks:
        if task["id"] == task_id:
            task["completed"] = request.completed
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found",
    )


@router.post(
    "/{transcript_id}/push-crm",
    summary="Push to CRM",
    description="Push transcript data to CRM (HubSpot).",
)
async def push_to_crm(transcript_id: str) -> Dict[str, Any]:
    """Push transcript to CRM."""
    if transcript_id not in _transcript_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript {transcript_id} not found",
        )

    stored = _transcript_store[transcript_id]

    # For MVP, we'll simulate CRM push - real implementation would use HubSpot API
    stored.crm_status = "synced"
    stored.crm_record_id = f"hubspot-{uuid4().hex[:8]}"

    return {
        "success": True,
        "recordId": stored.crm_record_id,
        "message": "Successfully pushed to CRM",
    }
