"""Transcript parsing and SPICED extraction API routes."""
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.models.transcript import (
    CallNote,
    FollowUpTask,
    TranscriptParseRequest,
    TranscriptParseResponse,
)
from app.models.spiced import SPICEDAnalysis
from app.services.claude_client import ClaudeClientError
from app.services.transcript import TranscriptParser, SPICEDExtractor

logger = logging.getLogger(__name__)

router = APIRouter()


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
