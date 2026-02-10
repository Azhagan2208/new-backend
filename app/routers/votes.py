from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..deps import get_db

router = APIRouter(tags=["Votes"])


@router.post("/questions/{question_id}/vote")
def vote_question(
    question_id: int, data: schemas.VoteCreate, db: Session = Depends(get_db)
):
    """Cast a vote on a question."""
    q = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    if data.vote_type not in ("up", "down"):
        raise HTTPException(status_code=400, detail="vote_type must be 'up' or 'down'")

    v = models.QuestionVote(
        question_id=question_id, voter_token=data.voter_token, vote_type=data.vote_type
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"success": True, "vote_id": v.id}
