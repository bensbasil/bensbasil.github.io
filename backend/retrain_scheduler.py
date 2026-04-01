from apscheduler.schedulers.background import BackgroundScheduler
import traceback
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ModelMeta, QuizResponse
from train import run_training
from utils.model_loader import model_loader
from datetime import datetime
import pytz

def check_and_retrain():
    """
    Checks if there are new Quiz Responses since the last trained model.
    If yes, triggers retraining.
    """
    db = SessionLocal()
    try:
        latest_model = db.query(ModelMeta).order_by(ModelMeta.trained_at.desc()).first()
        if latest_model:
            # Check if any responses came after this model was trained
            new_responses = db.query(QuizResponse).filter(QuizResponse.created_at > latest_model.trained_at).count()
            if new_responses == 0:
                print("No new responses to train on. Skipping retraining.")
                return
            print(f"[{datetime.now()}] Found {new_responses} new responses. Initiating retrain...")
        else:
            # Check if we have enough total responses to train the first time
            count = db.query(QuizResponse).count()
            if count < 5:
                print("Not enough total responses (< 5) for initial training. Skipping.")
                return
            print(f"[{datetime.now()}] Initiating first training run...")
        
        # Trigger actual train process
        run_training()
        
        # Reload live models so requests immediately use new pkls
        model_loader.load_latest_models()
        
    except Exception as e:
        print(f"Retrain check failed: {traceback.format_exc()}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    # Step 3: Add a cron job inside Docker: retrain every 60 minutes
    scheduler.add_job(check_and_retrain, 'interval', minutes=60)
    scheduler.start()
    print("Background retrain scheduler started - interval: 60 minutes.")
    return scheduler
