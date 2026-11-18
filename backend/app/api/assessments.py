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
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/", response_model=AssessmentListResponse)
def list_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessments, total = get_assessments(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    return AssessmentListResponse(
        total=total,
        assessments=assessments,
        skip=skip,
        limit=limit,
    )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def retrieve_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = get_assessment_by_id(
        db=db,
        assessment_id=assessment_id,
        user_id=current_user.id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    return assessment
