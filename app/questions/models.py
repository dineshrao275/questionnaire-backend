from sqlalchemy import (
    Column,
    String,
    Boolean,
    JSON,
    ForeignKey,
    Integer,
    DateTime,
    Text,
)
from datetime import datetime
from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(String, nullable=False)
    type = Column(
        String, nullable=False
    )  # text, number, date, single_choice, multiple_choice
    required = Column(Boolean, default=True)
    options = Column(JSON, nullable=True)  # For choice questions
    correct_answer = Column(JSON, nullable=True)  # String or array
    next_question_mapping = Column(
        JSON, nullable=False
    )  # Dict mapping answers to next question IDs
    validation_rules = Column(JSON, nullable=True)  # Dict with validation rules


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    answer_value = Column(JSON, nullable=True)  # String or array
    is_correct = Column(Boolean, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    sequence_number = Column(
        Integer, nullable=False
    )  # Position in user's question sequence

    # Relationships
    question = relationship("Question")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    current_question_id = Column(String, ForeignKey("questions.id"), nullable=True)
    completed_questions = Column(JSON, default=list)  # Array of question IDs
    question_path = Column(JSON, default=list)  # Ordered array of question IDs
    start_time = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    is_completed = Column(Boolean, default=False)


class QuestionPath(Base):
    __tablename__ = "question_paths"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    question_sequence = Column(
        JSON, default=list
    )  # Array of dict objects with sequence details


# Pydantic models for API
class QuestionResponse(BaseModel):
    id: str
    text: str
    type: str
    required: bool
    options: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AnswerCreate(BaseModel):
    question_id: str
    answer_value: Union[str, List[str], int, float, None]


class AnswerResponse(BaseModel):
    id: str
    question_id: str
    answer_value: Any
    is_correct: Optional[bool] = None
    timestamp: datetime
    sequence_number: int

    class Config:
        from_attributes = True


class NextQuestionResponse(BaseModel):
    question: Optional[QuestionResponse] = None
    is_last: bool = False

    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    current_question_id: Optional[str]
    completed_questions: List[str]
    question_path: List[str]
    start_time: datetime
    last_activity: datetime
    is_completed: bool
    completion_percentage: float

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    user_answers: List[Dict[str, Any]]
    start_time: datetime
    completion_time: Optional[datetime]
    completion_percentage: float

    class Config:
        from_attributes = True
