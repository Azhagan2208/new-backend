from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..deps import get_db, get_current_teacher

router = APIRouter(tags=["Questions"])


@router.post("/rooms/{room_id}/questions", response_model=schemas.QuestionOut)
def post_question(
    room_id: int, data: schemas.QuestionCreate, db: Session = Depends(get_db)
):
    """Post a new question to a room."""
    room = (
        db.query(models.Room)
        .filter(models.Room.id == room_id, models.Room.is_open == True)
        .first()
    )

    if not room:
        raise HTTPException(status_code=404, detail="Room not found or closed")

    q = models.Question(
        room_id=room_id,
        title=data.title,
        description=data.description,
        student_name=data.student_name,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/rooms/{room_id}/questions", response_model=schemas.QuestionListResponse)
def list_room_questions(
    room_id: int, db: Session = Depends(get_db), sort: str = "recent"
):
    """List all questions in a room with vote counts."""
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    questions_query = (
        db.query(models.Question).filter(models.Question.room_id == room_id).all()
    )

    results = []
    for q in questions_query:
        # Count upvotes
        vote_count = (
            db.query(models.QuestionVote)
            .filter(
                models.QuestionVote.question_id == q.id,
                models.QuestionVote.vote_type == "up",
            )
            .count()
        )

        q_out = schemas.QuestionOut.model_validate(q)
        q_out.votes = vote_count
        results.append(q_out)

    # Sorting
    if sort == "votes":
        results.sort(key=lambda x: x.votes, reverse=True)
    else:
        results.sort(key=lambda x: x.created_at, reverse=True)

    return {"success": True, "questions": results}


@router.post("/questions/{question_id}/solve", response_model=schemas.QuestionOut)
def mark_solved(
    question_id: int,
    db: Session = Depends(get_db),
    teacher: models.Teacher = Depends(get_current_teacher),
):
    """Mark a question as solved (Only for the room owner)."""
    q = (
        db.query(models.Question)
        .join(models.Room)
        .filter(models.Question.id == question_id, models.Room.owner_id == teacher.id)
        .first()
    )

    if not q:
        raise HTTPException(
            status_code=403, detail="Not authorized to mark this question as solved"
        )

    q.is_solved = True
    db.commit()
    db.refresh(q)
    return q
