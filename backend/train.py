import os
import glob
import numpy as np
import joblib
from datetime import datetime
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sqlalchemy.orm import Session
from database import SessionLocal
from models import QuizResponse, ModelMeta

# Mappings for DISC stress logic
PRIMARY_TO_STRESS_MAP = {
    "red": "yellow",   # Fire -> Air
    "yellow": "red",   # Air  -> Fire
    "green": "blue",   # Earth -> Water
    "blue": "green"    # Water -> Earth
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), "ml", "models")
MAX_VERSIONS = 5



def derive_stress_type(color_scores, dominant_color, secondary_color):
    """
    Derives the stress type using DISC theory rules.
    If secondary score is within 10% of primary, stress flips to secondary.
    Otherwise, follows the standard flip rules.
    """
    total = sum(color_scores.values()) or 1
    primary_score = color_scores.get(dominant_color, 0)
    secondary_score = color_scores.get(secondary_color, 0)
    
    # If the secondary score is within 10% of the total score from the primary score
    # meaning the difference is <= 10% of the total response vector
    if (primary_score - secondary_score) / total <= 0.10:
        return secondary_color
    
    return PRIMARY_TO_STRESS_MAP.get(dominant_color, dominant_color)

def build_feature_matrix(responses):
    """Build feature matrix for primary and stress models."""
    X = []
    y_dominant = []
    y_stress = []

    for r in responses:
        answers = r.answers
        scores = r.color_scores
        total = sum(scores.values()) or 1
        score_vector = [
            scores.get("red", 0) / total,
            scores.get("yellow", 0) / total,
            scores.get("green", 0) / total,
            scores.get("blue", 0) / total,
        ]
        X.append(answers + score_vector)
        y_dominant.append(r.dominant_color)
        
        stress_color = derive_stress_type(scores, r.dominant_color, r.secondary_color)
        y_stress.append(stress_color)

    return np.array(X, dtype=float), np.array(y_dominant), np.array(y_stress)

def get_next_version(db: Session):
    latest = db.query(ModelMeta).order_by(ModelMeta.version.desc()).first()
    return (latest.version + 1) if latest else 1

def cleanup_old_models(db: Session, model_type: str):
    versions = db.query(ModelMeta).filter(ModelMeta.model_type == model_type).order_by(ModelMeta.version.desc()).all()
    if len(versions) > MAX_VERSIONS:
        to_delete = versions[MAX_VERSIONS:]
        for entry in to_delete:
            model_path = os.path.join(MODELS_DIR, f"model_{model_type}_v{entry.version}.pkl")
            if os.path.exists(model_path):
                os.remove(model_path)
            db.delete(entry)
        db.commit()

def run_training():
    os.makedirs(MODELS_DIR, exist_ok=True)
    db = SessionLocal()
    
    try:
        responses = db.query(QuizResponse).all()
        sample_count = len(responses)
        if sample_count < 5:
            print("Not enough samples to train.")
            return

        X, y_dominant, y_stress = build_feature_matrix(responses)
        new_version = get_next_version(db)
        
        # 1) Train Primary Model (GaussianNB)
        le_primary = LabelEncoder()
        y_dom_encoded = le_primary.fit_transform(y_dominant)
        
        clf_primary = GaussianNB()
        if sample_count < 10:
            clf_primary.fit(X, y_dom_encoded)
            acc_primary = 1.0
        else:
            X_train, X_test, y_train, y_test = train_test_split(X, y_dom_encoded, test_size=0.2, random_state=42)
            clf_primary.fit(X_train, y_train)
            acc_primary = accuracy_score(y_test, clf_primary.predict(X_test))
        
        # 2) Train Stress Model (LogisticRegression)
        le_stress = LabelEncoder()
        y_stress_encoded = le_stress.fit_transform(y_stress)
        
        clf_stress = LogisticRegression(max_iter=1000)
        if sample_count < 10:
            clf_stress.fit(X, y_stress_encoded)
            acc_stress = 1.0
        else:
            X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X, y_stress_encoded, test_size=0.2, random_state=42)
            clf_stress.fit(X_train_s, y_train_s)
            acc_stress = accuracy_score(y_test_s, clf_stress.predict(X_test_s))

        # Save Pickles
        joblib.dump({"model": clf_primary, "le": le_primary}, os.path.join(MODELS_DIR, f"model_primary_v{new_version}.pkl"))
        joblib.dump({"model": clf_stress, "le": le_stress}, os.path.join(MODELS_DIR, f"model_stress_v{new_version}.pkl"))
        
        # Update DB Metadata
        db.add(ModelMeta(
            version=new_version,
            model_type="primary",
            accuracy=acc_primary,
            sample_count=sample_count
        ))
        db.add(ModelMeta(
            version=new_version,
            model_type="stress",
            accuracy=acc_stress,
            sample_count=sample_count
        ))
        db.commit()
        
        # Cleanup old
        cleanup_old_models(db, "primary")
        cleanup_old_models(db, "stress")
        
        print(f"V{new_version} trained | Primary acc: {acc_primary:.3f} | Stress acc: {acc_stress:.3f} | Samples: {sample_count}")
            
    except Exception as e:
        print(f"Error during training: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_training()
