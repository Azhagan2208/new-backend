from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Authentication & Teacher Request Schemas ---


class TeacherRequestCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class TeacherOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str


# --- Room Schemas ---


class RoomCreate(BaseModel):
    title: str


class RoomOut(BaseModel):
    id: int
    title: str
    room_code: str
    owner_id: int
    is_open: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    success: bool
    room: RoomOut


# --- Question Schemas ---


class QuestionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    student_name: Optional[str] = None


class QuestionOut(BaseModel):
    id: int
    room_id: int
    title: str
    description: Optional[str]
    student_name: Optional[str]
    created_at: datetime
    is_solved: bool
    votes: int = 0

    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    success: bool
    questions: List[QuestionOut]


# --- Vote Schemas ---


class VoteCreate(BaseModel):
    vote_type: str
    voter_token: Optional[str] = None
