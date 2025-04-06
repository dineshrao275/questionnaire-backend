from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine, Base
from app.auth.router import router as auth_router
from app.questions.router import router as questions_router
from app.config import settings

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(questions_router)


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Add sample questions on startup
@app.on_event("startup")
async def create_initial_data():
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.questions.models import Question
    import uuid

    db = SessionLocal()

    # Check if we have any questions
    question_count = db.query(Question).count()

    if question_count == 0:
        # Create initial questions
        questions = [
            Question(
                id=str(uuid.uuid4()),
                text="Which smartphone operating system do you prefer?",
                type="single_choice",
                required=True,
                options=["iOS", "Android", "Other"],
                next_question_mapping={
                    "iOS": "q2",  # We'll update these IDs after creating all questions
                    "Android": "q3",
                    "Other": "q4",
                    "default": "q5",
                },
                validation_rules={"min_length": 1},
            ),
            Question(
                id="q2",  # Temporary ID
                text="Which iPhone model do you currently use?",
                type="single_choice",
                required=True,
                options=[
                    "iPhone 14 or newer",
                    "iPhone 11-13",
                    "iPhone X-8",
                    "iPhone 7 or older",
                    "I don't use an iPhone",
                ],
                next_question_mapping={"default": "q5"},
                validation_rules={"min_length": 1},
            ),
            Question(
                id="q3",  # Temporary ID
                text="Which Android brand do you prefer?",
                type="single_choice",
                required=True,
                options=["Samsung", "Google", "OnePlus", "Xiaomi", "Other"],
                next_question_mapping={"default": "q5"},
                validation_rules={"min_length": 1},
            ),
            Question(
                id="q4",  # Temporary ID
                text="Why don't you prefer mainstream smartphone operating systems?",
                type="text",
                required=True,
                next_question_mapping={"default": "q5"},
                validation_rules={"min_length": 10, "max_length": 500},
            ),
            Question(
                id="q5",  # Temporary ID
                text="How many hours per day do you spend on your smartphone?",
                type="number",
                required=True,
                next_question_mapping={"default": "q6"},
                validation_rules={"min": 0, "max": 24},
            ),
            Question(
                id="q6",  # Temporary ID
                text="Which features are most important to you when choosing a smartphone?",
                type="multiple_choice",
                required=True,
                options=[
                    "Camera quality",
                    "Battery life",
                    "Processing speed",
                    "Storage capacity",
                    "Screen size",
                    "Price",
                    "Brand",
                ],
                next_question_mapping={"default": "q7"},
                validation_rules={"min_choices": 1, "max_choices": 3},
            ),
            Question(
                id="q7",  # Temporary ID
                text="When did you purchase your current smartphone?",
                type="date",
                required=True,
                next_question_mapping={"default": "q8"},
                validation_rules={},
            ),
            Question(
                id="q8",  # Temporary ID
                text="How satisfied are you with your current smartphone on a scale of 1-10?",
                type="number",
                required=True,
                next_question_mapping={"default": "q9"},
                validation_rules={"min": 1, "max": 10},
            ),
            Question(
                id="q9",  # Temporary ID
                text="What is your primary use case for your smartphone?",
                type="single_choice",
                required=True,
                options=[
                    "Social media",
                    "Gaming",
                    "Work/productivity",
                    "Photography",
                    "Communication",
                    "Web browsing",
                ],
                next_question_mapping={"default": "q10"},
                validation_rules={"min_length": 1},
            ),
            Question(
                id="q10",  # Temporary ID
                text="Would you recommend your current smartphone to others?",
                type="single_choice",
                required=True,
                options=["Yes", "No", "Maybe"],
                next_question_mapping={"default": None},  # End of questionnaire
                validation_rules={"min_length": 1},
            ),
        ]

        # Update question IDs and mappings
        for i, question in enumerate(questions):
            if i > 0:  # Skip the first one which already has a String
                uuid_id = str(uuid.uuid4())
                # Update next_question_mapping references in previous questions
                for prev_q in questions:
                    for key, value in prev_q.next_question_mapping.items():
                        if value == question.id:
                            prev_q.next_question_mapping[key] = uuid_id

                # Update the ID
                question.id = uuid_id

        # Add all questions to the database
        for question in questions:
            db.add(question)

        db.commit()
        print("Initial questions created")

    db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
