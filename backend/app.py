from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv
load_dotenv()

import os
import models
import schemas
from database import engine, get_db
from ml.predictor import get_analytics
from utils.model_loader import model_loader
from retrain_scheduler import start_scheduler
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional, Dict
import bcrypt
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from prometheus_fastapi_instrumentator import Instrumentator

# Define Prometheus Custom Metrics
prediction_requests_total = Counter(
    "prediction_requests_total",
    "Total number of prediction requests",
    ["model_type", "result"]
)
prediction_confidence_histogram = Histogram(
    "prediction_confidence_histogram",
    "Histogram of prediction confidences",
    ["model_type"]
)
active_model_version = Gauge(
    "active_model_version",
    "Currently active ML model version",
    ["model_type"]
)
db_response_count = Gauge(
    "db_response_count",
    "Total response rows in the database"
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "513027492748-8mja1qbgip3k0ernd217a2ido6sc18gu.apps.googleusercontent.com")

# Load environment variables

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

# Instrument the app for Prometheus metrics
Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
def startup_event():
    start_scheduler()


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
    background_tasks: BackgroundTasks,  
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

    db_response_count.set(db.query(models.QuizResponse).count())

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

@app.post("/predict/stress", response_model=schemas.StressResult)
def predict_stress(payload: schemas.StressPredictRequest, db: Session = Depends(get_db)):
    # Update total DB response track
    response_count = db.query(models.QuizResponse).count()
    db_response_count.set(response_count)
    
    # Check model
    if not model_loader.models_exist():
        raise HTTPException(status_code=503, detail="Stress model not yet trained")
    
    # Track version
    active_model_version.labels(model_type="stress").set(model_loader.stress_version or 0)
    
    # Format X vector
    total = sum(payload.color_scores.values()) or 1
    scores = payload.color_scores
    score_vector = [
        scores.get("red", 0) / total,
        scores.get("yellow", 0) / total,
        scores.get("green", 0) / total,
        scores.get("blue", 0) / total,
    ]
    X = [payload.answers + score_vector]
    
    label, conf = model_loader.predict_stress(X)
    
    prediction_requests_total.labels(model_type="stress", result=label).inc()
    prediction_confidence_histogram.labels(model_type="stress").observe(conf)
    
    # Stress Descriptions
    DESCRIPTIONS = {
        "red": "You become forceful, quick-tempered, and focus heavily on results over people to maintain control.",
        "yellow": "You act emotionally expressive, disorganized, and try to talk your way out of difficult situations.",
        "green": "You go quiet, over-accommodate, and avoid conflict to keep the peace \u2014 often at your own expense.",
        "blue": "You get perfectionistic, defensive, and withdraw into analysis paralysis trying to avoid mistakes."
    }
    desc = DESCRIPTIONS.get(label, "You shift to this type under pressure.")
    
    return schemas.StressResult(
        stress_type=label,
        stress_label=label.capitalize(),
        stress_description=desc,
        confidence=conf
    )

@app.post("/auth/google", response_model=schemas.UserProfileResponse)
def google_auth(payload: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    # 1. Verify the Google ID token
    try:
        id_info = id_token.verify_oauth2_token(
            payload.google_token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token.")
 
    google_id    = id_info.get("sub")
    email        = id_info.get("email")
    display_name = id_info.get("name")
    avatar_url   = id_info.get("picture")
 
    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token.")
 
    # 2. Find or create user
    user = db.query(models.User).filter(models.User.email == email).first()
    is_new = False
 
    if not user:
        is_new = True
        user = models.User(
            email        = email,
            google_id    = google_id,
            display_name = display_name,
            avatar_url   = avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
 
    # 3. Save quiz result if attached
    if payload.quiz_result and payload.quiz_result.get("dominant_color"):
        user.dominant_color = payload.quiz_result.get("dominant_color")
        user.secondary_color= payload.quiz_result.get("secondary_color")
        user.color_scores   = payload.quiz_result.get("color_scores")
        user.answer_vector  = payload.quiz_result.get("answer_vector")
        db.commit()
        db.refresh(user)
 
    return schemas.UserProfileResponse(
        email          = user.email,
        display_name   = user.display_name,
        avatar_url     = user.avatar_url,
        dominant_color = user.dominant_color,
        secondary_color= user.secondary_color,
        color_scores   = user.color_scores,
        has_password   = user.password_hash is not None,
        is_new_user    = is_new,
    )
 
 
@app.post("/auth/set-password")
def set_password(payload: schemas.SetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
 
    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt())
    user.password_hash = hashed.decode()
    db.commit()
    return {"success": True, "message": "Password saved."}
 
 
@app.post("/auth/save-result")
def save_result(payload: schemas.SaveResultRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
 
    user.dominant_color = payload.dominant_color
    user.secondary_color= payload.secondary_color
    user.color_scores   = payload.color_scores
    user.answer_vector  = payload.answer_vector
    db.commit()
    return {"success": True}
 
 
@app.get("/auth/profile/{email}", response_model=schemas.UserProfileResponse)
def get_profile(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found.")
 
    return schemas.UserProfileResponse(
        email          = user.email,
        display_name   = user.display_name,
        avatar_url     = user.avatar_url,
        dominant_color = user.dominant_color,
        secondary_color= user.secondary_color,
        color_scores   = user.color_scores,
        has_password   = user.password_hash is not None,
    )


# ── health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    responses = db.query(models.QuizResponse).count()
    latest_meta = db.query(models.ModelMeta).order_by(models.ModelMeta.trained_at.desc()).first()
    last_trained = latest_meta.trained_at if latest_meta else None
    
    return {
        "status": "ok",
        "primary_model_version": model_loader.primary_version,
        "stress_model_version": model_loader.stress_version,
        "total_responses": responses,
        "last_trained_at": last_trained
    }