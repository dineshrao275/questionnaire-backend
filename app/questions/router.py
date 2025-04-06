from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db
from app.auth.router import get_current_user
from app.auth.models import User
from app.questions.models import (
    Question,
    UserAnswer,
    UserProgress,
    QuestionPath,
    QuestionResponse,
    AnswerCreate,
    AnswerResponse,
    NextQuestionResponse,
    ProgressResponse,
    SummaryResponse,
)

router = APIRouter(prefix="/api", tags=["questionnaire"])


# Get initial question
@router.get("/questions/start", response_model=QuestionResponse)
def get_initial_question(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Check if user has existing progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )

    if progress and progress.is_completed:
        # If questionnaire is completed, delete all answers and start fresh
        db.query(UserAnswer).filter(UserAnswer.user_id == current_user.id).delete()
        progress.completed_questions = []
        progress.question_path = []
        progress.is_completed = False
        progress.start_time = datetime.now()
        progress.last_activity = datetime.now()
        db.commit()

    # Get the first question
    first_question = db.query(Question).first()

    if not first_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No questions available"
        )

    # Create or update user progress
    if progress:
        progress.current_question_id = first_question.id
        progress.question_path = [str(first_question.id)]
    else:
        progress = UserProgress(
            user_id=current_user.id,
            current_question_id=first_question.id,
            question_path=[str(first_question.id)],
            completed_questions=[],
            is_completed=False,
            start_time=datetime.now(),
            last_activity=datetime.now()
        )
        db.add(progress)

    db.commit()
    return first_question


# Get specific question
@router.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    return question


# Submit answer and get next question
@router.post("/answers", response_model=NextQuestionResponse)
def submit_answer(
    answer_data: AnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get the question
    question = db.query(Question).filter(Question.id == answer_data.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    # Get user progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found"
        )

    # Check if the answer is correct (if applicable)
    is_correct = None
    if question.correct_answer is not None:
        is_correct = answer_data.answer_value == question.correct_answer

    # Get sequence number (position in user's question path)
    sequence_number = len(progress.completed_questions) + 1

    # Store the answer
    user_answer = UserAnswer(
        user_id=current_user.id,
        question_id=question.id,
        answer_value=answer_data.answer_value,
        is_correct=is_correct,
        sequence_number=sequence_number,
    )
    db.add(user_answer)

    # Update progress - Add question to completed questions
    if str(question.id) not in progress.completed_questions:
        progress.completed_questions.append(str(question.id))
    progress.last_activity = datetime.now()

    # Determine next question based on answer
    next_question_id = None
    answer_str = str(answer_data.answer_value)

    if answer_str in question.next_question_mapping:
        next_question_id = question.next_question_mapping[answer_str]
    elif "default" in question.next_question_mapping:
        next_question_id = question.next_question_mapping["default"]

    # Check if there's a next question or if this is the last one
    is_last = False
    next_question = None

    if next_question_id:
        next_question = (
            db.query(Question).filter(Question.id == next_question_id).first()
        )
        if next_question:
            progress.current_question_id = next_question.id
            if str(next_question.id) not in progress.question_path:
                progress.question_path.append(str(next_question.id))

    # If there's no next question or we've reached the limit (10 questions), mark as completed
    if not next_question or len(progress.completed_questions) >= 10:
        progress.is_completed = True
        progress.current_question_id = None
        is_last = True

    db.commit()

    next_question_data = (
        QuestionResponse.from_orm(next_question) if next_question else None
    )
    
    return NextQuestionResponse(question=next_question_data, is_last=is_last)


# Update answer for a specific question
@router.put("/answers/{question_id}", response_model=NextQuestionResponse)
def update_answer(
    question_id: str,
    answer_data: AnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    # Get user progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found"
        )

    # Find the existing answer
    user_answer = (
        db.query(UserAnswer)
        .filter(
            UserAnswer.user_id == current_user.id, UserAnswer.question_id == question_id
        )
        .first()
    )

    # Update or create answer
    if user_answer:
        # Check if the answer is correct (if applicable)
        if question.correct_answer is not None:
            user_answer.is_correct = answer_data.answer_value == question.correct_answer

        user_answer.answer_value = answer_data.answer_value
        user_answer.timestamp = datetime.now()
    else:
        # Get sequence number
        sequence_number = progress.question_path.index(question_id) + 1

        # Create new answer
        is_correct = None
        if question.correct_answer is not None:
            is_correct = answer_data.answer_value == question.correct_answer

        user_answer = UserAnswer(
            user_id=current_user.id,
            question_id=question.id,
            answer_value=answer_data.answer_value,
            is_correct=is_correct,
            sequence_number=sequence_number,
        )
        db.add(user_answer)

    # Recalculate question flow from this point forward
    # Get the index of the current question in the path
    try:
        current_index = progress.question_path.index(question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question not found in user's path",
        )

    # Keep only the questions up to and including the current one
    progress.question_path = progress.question_path[: current_index + 1]

    # Remove completed questions that come after this one
    progress.completed_questions = [
        q
        for q in progress.completed_questions
        if progress.question_path.index(q) <= current_index
    ]

    # Update last activity
    progress.last_activity = datetime.now()

    # Determine next question based on the new answer
    next_question_id = None
    answer_str = str(answer_data.answer_value)

    if answer_str in question.next_question_mapping:
        next_question_id = question.next_question_mapping[answer_str]
    elif "default" in question.next_question_mapping:
        next_question_id = question.next_question_mapping["default"]

    # Check if there's a next question
    is_last = False
    next_question = None

    if next_question_id:
        next_question = (
            db.query(Question).filter(Question.id == next_question_id).first()
        )
        if next_question:
            progress.current_question_id = next_question.id
            progress.question_path.append(str(next_question.id))
    else:
        # No next question
        progress.is_completed = True
        progress.current_question_id = None
        is_last = True

    db.commit()

    return NextQuestionResponse(question=next_question, is_last=is_last)


# Get previous question
@router.get("/questions/previous/{current_question_id}", response_model=QuestionResponse)
def get_previous_question(
    current_question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get user progress
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id)
        .first()
    )
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress found for user"
        )

    # Find the current question's index in the path
    try:
        current_index = progress.question_path.index(current_question_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current question not found in path"
        )

    # If this is the first question, we can't go back
    if current_index == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already at first question"
        )

    # Get the previous question ID from the path
    previous_question_id = progress.question_path[current_index - 1]

    # Get the previous question
    previous_question = (
        db.query(Question)
        .filter(Question.id == previous_question_id)
        .first()
    )

    if not previous_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Previous question not found"
        )

    # Update progress to point to the previous question
    progress.current_question_id = previous_question.id
    progress.question_path = progress.question_path[:current_index]
    progress.is_completed = False
    db.commit()

    return previous_question


# Get user progress
@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Get user progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found"
        )

    # Get all answers for completed questions
    answers = {}
    for question_id in progress.completed_questions:
        answer = (
            db.query(UserAnswer)
            .filter(
                UserAnswer.user_id == current_user.id,
                UserAnswer.question_id == question_id,
            )
            .first()
        )
        if answer:
            answers[question_id] = answer.answer_value

    # Calculate completion percentage based on completed questions
    total_questions = 10  # Fixed total questions
    completed = len(progress.completed_questions)
    completion_percentage = (completed / total_questions) * 100

    # Ensure we have all 10 questions in the path
    if len(progress.question_path) < total_questions:
        # Get the next questions based on the last answer
        last_question_id = progress.question_path[-1] if progress.question_path else None
        if last_question_id:
            last_question = db.query(Question).filter(Question.id == last_question_id).first()
            if last_question and last_question.next_question_mapping:
                next_question_id = last_question.next_question_mapping.get("default")
                if next_question_id and next_question_id not in progress.question_path:
                    progress.question_path.append(next_question_id)
                    db.commit()

    return {
        "completed_questions": progress.completed_questions,
        "question_path": progress.question_path,
        "is_completed": progress.is_completed,
        "completion_percentage": completion_percentage,
        "current_question_id": progress.current_question_id,
        "start_time": progress.start_time,
        "last_activity": progress.last_activity,
        "answers": answers,
        "total_questions": total_questions
    }


# Get summary of user's answers
@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Get user progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found"
        )

    # Get all user answers
    user_answers = (
        db.query(UserAnswer)
        .filter(UserAnswer.user_id == current_user.id)
        .order_by(UserAnswer.sequence_number)
        .all()
    )

    # Format the answers with question text
    formatted_answers = []
    for answer in user_answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        formatted_answers.append(
            {
                "question_id": str(answer.question_id),
                "question_text": question.text if question else "Unknown Question",
                "answer_value": answer.answer_value,
                "is_correct": answer.is_correct,
                "sequence_number": answer.sequence_number,
            }
        )

    # Calculate completion percentage
    total_questions = 10
    completed = len(progress.completed_questions)
    completion_percentage = (completed / total_questions) * 100

    return {
        "user_answers": formatted_answers,
        "start_time": progress.start_time,
        "completion_time": progress.last_activity if progress.is_completed else None,
        "completion_percentage": completion_percentage,
    }


# Get user's full question path history
@router.get("/question-history", response_model=List[str])
def get_question_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    # Get user progress
    progress = (
        db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found"
        )

    return progress.question_path
