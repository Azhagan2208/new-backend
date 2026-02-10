from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import random
import string
from typing import List

from .. import models, schemas
from ..deps import get_db, get_current_teacher

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

    return room


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
