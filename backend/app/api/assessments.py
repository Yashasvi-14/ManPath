from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import (
    AssessmentListResponse,
    AssessmentResponse,
)
from app.services.assessment_service import (
    get_assessments,
    get_assessment_by_id,
)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("", response_model=AssessmentListResponse)
def list_assessments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    assessments = get_assessments(
        db=db,
        skip=skip,
        limit=limit,
    )

    total = db.scalar(select(func.count()).select_from(Assessment))

    return AssessmentListResponse(
        assessments=assessments,
        total=total or 0,
        skip=skip,
        limit=limit,
    )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def retrieve_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
):
    assessment = get_assessment_by_id(
        db=db,
        assessment_id=assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    return assessment
