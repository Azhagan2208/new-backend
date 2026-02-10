from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TeacherRequest(Base):
    __tablename__ = "teacher_requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved = Column(Boolean, default=False)


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    room_code = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Teacher")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    student_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_solved = Column(Boolean, default=False)

    room = relationship("Room")


class QuestionVote(Base):
    __tablename__ = "question_votes"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    voter_token = Column(String, nullable=True)
    vote_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
