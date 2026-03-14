from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv
import os
import models
import schemas
from database import engine, get_db

# Load environment variables (from .env file if present)
load_dotenv()

# Configure FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "bensdbasil@gmail.com"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM = os.getenv("MAIL_FROM", "bensdbasil@gmail.com"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Portfolio Contact Form"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# Create the FastAPI app
app = FastAPI(title="Portfolio Backend API")

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"  # Allows all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/contact", response_model=schemas.ContactSubmissionResponse)
def create_contact_submission(
    submission: schemas.ContactSubmissionCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. Save to Database
    db_submission = models.ContactSubmission(
        name=submission.name,
        email=submission.email,
        message=submission.message
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    
    # 2. Prepare the Email Content
    html = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {submission.name}</p>
    <p><strong>Email:</strong> {submission.email}</p>
    <p><strong>Message:</strong></p>
    <blockquote style="border-left: 4px solid #00C0B5; padding-left: 10px; color: #555;">
        {submission.message}
    </blockquote>
    """
    
    # 3. Configure the Message Schema
    # Send it to YOUR email address, NOT the submitters!
    message = MessageSchema(
        subject=f"[Inquiry #{db_submission.id}] Portfolio Inquiry from {submission.name}",
        recipients=[os.getenv("MAIL_FROM", "bensdbasil@gmail.com")], 
        body=html,
        subtype=MessageType.html
    )

    # 4. Add the send_email task to the background queue
    if conf.MAIL_PASSWORD:
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)
    else:
        print("Warning: MAIL_PASSWORD is not set in .env. Email will not be sent.")

    return db_submission

@app.get("/health")
def health_check():
    return {"status": "ok"}
