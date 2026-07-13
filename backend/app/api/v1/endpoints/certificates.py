from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.crud import crud_certificate, crud_progress
from app.db.session import get_db
from app.models.user import User
from app.schemas.certificate import (
    CertificateGenerate,
    CertificateResponse,
    CertificateVerify,
)

router = APIRouter(prefix="/certificates", tags=["certificates"])
logger = get_logger(__name__)


@router.get("/me", response_model=list[CertificateResponse])
def get_my_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_certificate.get_by_user(db, user_id=current_user.id)


@router.post(
    "/generate",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_certificate(
    obj_in: CertificateGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if certificate already issued
    already_issued = crud_certificate.exists(
        db,
        user_id=current_user.id,
        specialization_id=obj_in.specialization_id,
    )
    if already_issued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate already issued for this specialization",
        )

    # Check progress exists and is completed
    progress = crud_progress.get_by_user_spec(
        db,
        user_id=current_user.id,
        specialization_id=obj_in.specialization_id,
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must explore this specialization before earning a certificate",
        )

    # Check quiz passed
    pass_threshold = 70
    if progress.quiz_score is None or progress.quiz_score < pass_threshold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You must pass the quiz with at least {pass_threshold}% to earn a certificate",
        )

    # Mark progress as completed and issue certificate
    crud_progress.mark_completed(db, db_obj=progress)
    certificate = crud_certificate.create(
        db,
        user_id=current_user.id,
        specialization_id=obj_in.specialization_id,
    )
    logger.info(
        f"Certificate issued to {current_user.email} "
        f"for specialization {obj_in.specialization_id} "
        f"— code: {certificate.certificate_code}"
    )
    return certificate


@router.get("/verify/{code}", response_model=CertificateVerify)
def verify_certificate(code: str, db: Session = Depends(get_db)):
    certificate = crud_certificate.get_by_code(db, code=code)
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found or invalid code",
        )
    return CertificateVerify(
        certificate_code=certificate.certificate_code,
        user_id=certificate.user_id,
        specialization_id=certificate.specialization_id,
        issued_at=certificate.issued_at,
    )