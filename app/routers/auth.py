from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app import models, schemas, security
from app.deps import get_db
from datetime import timedelta
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Configuration (In production, these should be in environment variables)
ADMIN_EMAIL = "admin@questup.com"
ADMIN_PASSWORD = "admin123"
ADMIN_SECRET = "questup_admin_secret_key_2024"


@router.post("/login")
def login(
    login_data: schemas.TeacherLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a teacher and return an access token."""
    teacher = (
        db.query(models.Teacher)
        .filter(models.Teacher.email == login_data.email)
        .first()
    )

    if not teacher or not security.verify_password(
        login_data.password, teacher.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": teacher.email}, expires_delta=access_token_expires
    )

    return {
        "success": True,
        "token": access_token,
        "teacher": {"id": teacher.id, "name": teacher.name, "email": teacher.email},
    }


@router.post("/teachers/request-access")
def request_access(
    request: schemas.TeacherRequestCreate, db: Session = Depends(get_db)
):
    """Submit a request for teacher access (requires admin approval)."""
    # Check if request already exists
    existing_request = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.email == request.email)
        .first()
    )
    if existing_request:
        raise HTTPException(status_code=400, detail="Request already pending")

    # Check if already a teacher
    existing_teacher = (
        db.query(models.Teacher).filter(models.Teacher.email == request.email).first()
    )
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.get_password_hash(request.password)
    new_request = models.TeacherRequest(
        name=request.name, email=request.email, password_hash=hashed_password
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {"success": True, "message": "Access request submitted successfully"}


@router.post("/teachers/admin/login")
def admin_login(login_data: schemas.TeacherLogin):
    """Simple admin login with hardcoded credentials."""
    if login_data.email == ADMIN_EMAIL and login_data.password == ADMIN_PASSWORD:
        return {"success": True, "token": ADMIN_SECRET}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials"
    )


@router.get("/teachers/requests")
def get_teacher_requests(
    db: Session = Depends(get_db), x_admin_secret: Optional[str] = Header(None)
):
    """Get list of pending and approved teacher requests (Admin only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret"
        )

    pending = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.approved == False)
        .all()
    )
    approved = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.approved == True)
        .all()
    )
    total_teachers = db.query(models.Teacher).count()

    return {
        "success": True,
        "requests": pending,
        "history": approved,
        "stats": {
            "pending": len(pending),
            "approved": len(approved),
            "total": total_teachers,
        },
    }


@router.post("/teachers/approve/{request_id}")
def approve_teacher(
    request_id: int,
    db: Session = Depends(get_db),
    x_admin_secret: Optional[str] = Header(None),
):
    """Approve a teacher request and create the teacher account (Admin only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret"
        )

    req = (
        db.query(models.TeacherRequest)
        .filter(models.TeacherRequest.id == request_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.approved:
        raise HTTPException(status_code=400, detail="Teacher already approved")

    # Create teacher from request
    teacher = models.Teacher(
        name=req.name, email=req.email, password_hash=req.password_hash
    )
    db.add(teacher)

    # Mark request as approved
    req.approved = True

    db.commit()
    return {"success": True, "message": "Teacher approved and account created"}
