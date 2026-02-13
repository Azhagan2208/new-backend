from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import random
import string
from typing import List

from app import models, schemas
from app.deps import get_db, get_current_teacher

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def gen_room_code():
    """Generate a unique 6-character alphanumeric room code."""
    # Using only letters and numbers for a clean code
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(6))


@router.post("", response_model=schemas.RoomResponse)
def create_room(
    data: schemas.RoomCreate,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    """Create a new room for a teacher."""
    code = gen_room_code()
    # Ensure unique room code
    while db.query(models.Room).filter(models.Room.room_code == code).first():
        code = gen_room_code()

    room = models.Room(
        title=data.title,
        room_code=code,
        owner_id=teacher.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return {"success": True, "room": room}


@router.get("/my-rooms", response_model=schemas.RoomListResponse)
def list_my_rooms(
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    """List all rooms created by the current teacher with counts."""
    rooms = db.query(models.Room).filter(models.Room.owner_id == teacher.id).all()

    results = []
    for room in rooms:
        # Count total questions
        question_count = (
            db.query(models.Question).filter(models.Question.room_id == room.id).count()
        )

        # Count unique students (participants)
        participant_count = (
            db.query(models.Question.student_name)
            .filter(models.Question.room_id == room.id)
            .distinct()
            .count()
        )

        results.append(
            {
                "id": room.id,
                "title": room.title,
                "room_code": room.room_code,
                "is_open": room.is_open,
                "created_at": room.created_at,
                "question_count": question_count,
                "participant_count": participant_count,
            }
        )

    # Sort rooms by created_at descending
    results.sort(key=lambda x: x["created_at"], reverse=True)

    return {"success": True, "rooms": results}


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    """Get details of a specific room."""
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Count total questions
    question_count = (
        db.query(models.Question).filter(models.Question.room_id == room.id).count()
    )

    # Count unique students (participants)
    participant_count = (
        db.query(models.Question.student_name)
        .filter(models.Question.room_id == room.id)
        .distinct()
        .count()
    )

    return {
        "id": room.id,
        "title": room.title,
        "room_code": room.room_code,
        "owner_id": room.owner_id,
        "is_open": room.is_open,
        "created_at": room.created_at,
        "question_count": question_count,
        "participant_count": participant_count,
    }


@router.post("/join", response_model=schemas.RoomResponse)
def join_by_code(payload: dict, db: Session = Depends(get_db)):
    """Join a room using a room code."""
    code = payload.get("room_code")
    if not code:
        raise HTTPException(status_code=400, detail="room_code required")

    room = (
        db.query(models.Room)
        .filter(models.Room.room_code == code, models.Room.is_open == True)
        .first()
    )

    if not room:
        raise HTTPException(status_code=404, detail="Room not found or closed")

    return {"success": True, "room": room}


@router.post("/{room_id}/close")
def close_room(
    room_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    """Close a room so no more questions can be posted."""
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.owner_id == teacher.id)
        .first()
    )

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.is_open = False
    db.commit()
    return {"success": True, "message": "Room closed successfully"}
