# FastAPI Backend Project

This is a backend project built using [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance) web framework for building APIs with Python 3.7+.

## Overview

The Dynamic Questionnaire Application is an interactive web platform that presents users with a series of questions one by one that dynamically adapt based on previous answers. Users will register, log in, and navigate through the question paths, ultimately receiving a summary report after 10 questions of their responses.

## Feature
1. Registration: New users create an account
2. Login: Registered users access their account
3. Questionnaire: Users answer dynamic questions that change based on previous responses
4. Summary Report: Users view a comprehensive summary of their answers upon completion

## Prerequisites

- Python 3.7 or higher
- `pip` (Python package manager)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/dineshroa275/questionnaire.git
    cd Questionnaire/backend
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1. Start the FastAPI server:

    ```bash
    uvicorn app.main:app --reload
    ```

   
2. Open your browser and navigate to:

    - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
    - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Project Structure

```
backend/                  # FastAPI backend
  ├── app/
  │   ├── __init__.py
  │   ├── main.py           # Main FastAPI application
  │   ├── auth/             # Authentication module
  │   │   ├── __init__.py
  │   │   ├── jwt.py        # JWT token handling
  │   │   ├── models.py     # User models
  │   │   └── router.py     # Auth endpoints
  │   ├── questions/        # Question module
  │   │   ├── __init__.py
  │   │   ├── models.py     # Question models
  │   │   └── router.py     # Question endpoints
  │   ├── answers/          # Answer module
  │   │   ├── __init__.py
  │   │   ├── models.py     # Answer models
  │   │   └── router.py     # Answer endpoints
  │   ├── database.py       # Database connection
  │   └── config.py         # Configuration settings
  ├── requirements.txt      # Python dependencies
  └── README.md             # Backend setup instructions
```
