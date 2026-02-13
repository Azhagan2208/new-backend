from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from sqlalchemy.orm import Session
from app import models, schemas, security
from app.deps import get_db
from datetime import timedelta
from typing import Optional
import io
from fpdf import FPDF

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


@router.get("/admin/teachers/{teacher_id}/rooms")
def get_teacher_rooms(
    teacher_id: int,
    db: Session = Depends(get_db),
    x_admin_secret: Optional[str] = Header(None),
):
    """Get all rooms for a specific teacher (Admin only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret"
        )

    rooms = db.query(models.Room).filter(models.Room.owner_id == teacher_id).all()

    results = []
    for room in rooms:
        # Count total questions
        question_count = (
            db.query(models.Question).filter(models.Question.room_id == room.id).count()
        )
        results.append(
            {
                "id": room.id,
                "title": room.title,
                "room_code": room.room_code,
                "created_at": room.created_at,
                "question_count": question_count,
            }
        )

    return {"success": True, "rooms": results}


@router.get("/admin/rooms/{room_id}/questions/download")
def download_room_questions(
    room_id: int,
    db: Session = Depends(get_db),
    x_admin_secret: Optional[str] = Header(None),
):
    """Download questions for a room as a PDF (Admin only)."""
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin secret"
        )

    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    questions = (
        db.query(models.Question)
        .filter(models.Question.room_id == room_id)
        .order_by(models.Question.created_at.desc())
        .all()
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Room: {room.title}", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Room Code: {room.room_code}", ln=True, align="C")
    pdf.ln(10)

    if not questions:
        pdf.cell(0, 10, "No questions found in this room.", ln=True)
    else:
        for i, q in enumerate(questions, 1):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Q{i}: {q.title}", ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, f"Description: {q.description or 'No description'}")
            pdf.cell(0, 8, f"Posted by: {q.student_name or 'Anonymous'}", ln=True)
            pdf.cell(
                0, 8, f"Date: {q.created_at.strftime('%Y-%m-%d %H:%M:%S')}", ln=True
            )
            pdf.cell(
                0, 8, f"Status: {'Solved' if q.is_solved else 'Unsolved'}", ln=True
            )
            pdf.ln(5)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(5)

    pdf_output = pdf.output(dest="S")

    headers = {
        "Content-Disposition": f'attachment; filename="room_{room.room_code}_questions.pdf"'
    }
    return Response(content=pdf_output, media_type="application/pdf", headers=headers)
