from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv
import os
import models
import schemas
from database import engine, get_db
from ml.predictor import get_analytics, score_response

# Load environment variables
load_dotenv()

# Create all tables
models.Base.metadata.create_all(bind=engine)

# Configure FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME   = os.getenv("MAIL_USERNAME", "bensdbasil@gmail.com"),
    MAIL_PASSWORD   = os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM       = os.getenv("MAIL_FROM", "bensdbasil@gmail.com"),
    MAIL_PORT       = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER     = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME  = os.getenv("MAIL_FROM_NAME", "Portfolio Contact Form"),
    MAIL_STARTTLS   = True,
    MAIL_SSL_TLS    = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS  = True
)

app = FastAPI(title="Portfolio Backend API")

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── existing contact route ────────────────────────────────────────────────────

@app.post("/contact", response_model=schemas.ContactSubmissionResponse)
def create_contact_submission(
    submission: schemas.ContactSubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_submission = models.ContactSubmission(
        name=submission.name,
        email=submission.email,
        message=submission.message
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    html = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {submission.name}</p>
    <p><strong>Email:</strong> {submission.email}</p>
    <p><strong>Message:</strong></p>
    <blockquote style="border-left: 4px solid #00C0B5; padding-left: 10px; color: #555;">
        {submission.message}
    </blockquote>
    """

    message = MessageSchema(
        subject=f"[Inquiry #{db_submission.id}] Portfolio Inquiry from {submission.name}",
        recipients=[os.getenv("MAIL_FROM", "bensdbasil@gmail.com")],
        body=html,
        subtype=MessageType.html
    )

    if conf.MAIL_PASSWORD:
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)
    else:
        print("Warning: MAIL_PASSWORD not set. Email will not be sent.")

    return db_submission


# ── quiz routes ───────────────────────────────────────────────────────────────

@app.post("/quiz/submit", response_model=schemas.QuizSubmitResponse)
def submit_quiz(
    payload: schemas.QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    # check for duplicate session — one submission per quiz attempt
    existing = db.query(models.QuizResponse).filter(
        models.QuizResponse.session_id == payload.session_id
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Session already submitted.")

    # save raw response to database
    db_response = models.QuizResponse(
        session_id      = payload.session_id,
        answers         = payload.answers,
        color_scores    = payload.color_scores,
        dominant_color  = payload.dominant_color,
        secondary_color = payload.secondary_color,
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    return schemas.QuizSubmitResponse(
        success    = True,
        message    = "Response saved successfully.",
        session_id = payload.session_id
    )


@app.get("/analytics", response_model=schemas.AnalyticsResponse)
def get_analytics_data(
    session_id: str = None,
    db: Session = Depends(get_db)
):
    all_responses = db.query(models.QuizResponse).all()

    if len(all_responses) < 5:
        raise HTTPException(
            status_code=202,
            detail="Not enough data yet. Need at least 5 responses to show analytics."
        )

    return get_analytics(all_responses, current_session_id=session_id)


@app.post("/ml/train")
def train_models(db: Session = Depends(get_db)):
    all_responses = db.query(models.QuizResponse).all()

    if len(all_responses) < 5:
        raise HTTPException(
            status_code=202,
            detail="Need at least 5 responses to train models."
        )

    from ml.trainer import train_all
    result = train_all(all_responses)

    return {
        "success": True,
        "responses_used": len(all_responses),
        "models_trained": result["models_trained"],
        "accuracy": result["accuracy"]
    }


# ── health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok"}