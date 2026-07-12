from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct: str
    explanation: Optional[str] = None


class QuizCreate(BaseModel):
    specialization_id: UUID
    title: str
    questions: List[QuizQuestion] = []
    pass_score: int = 70


class QuizResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    specialization_id: UUID
    title: str
    questions: List[Dict[str, Any]]
    pass_score: int
    created_at: datetime


class QuizSubmit(BaseModel):
    answers: Dict[str, str]  # {question_id: selected_option}


class QuizResult(BaseModel):
    score: int
    passed: bool
    pass_score: int
    correct: int
    total: int