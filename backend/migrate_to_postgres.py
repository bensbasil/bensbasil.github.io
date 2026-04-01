import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import models

# Source SQLite DB
SQLITE_URL = "sqlite:///./portfolio.db"
sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocalSqlite = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# Target Postgres DB
POSTGRES_URL = os.getenv("DATABASE_URL")
if not POSTGRES_URL or POSTGRES_URL.startswith("sqlite"):
    print("Error: DATABASE_URL not set to a Postgres connection string.")
    print("Example: DATABASE_URL='postgresql://admin:adminpassword@localhost:5432/portfolio_db' python migrate_to_postgres.py")
    print("If you are running this from outside Docker, map the port in docker-compose first and use localhost.")
    exit(1)

pg_engine = create_engine(POSTGRES_URL)
SessionLocalPg = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)

def migrate():
    print(f"Starting Migration from {SQLITE_URL} to Postgres...")
    
    # Ensure tables exist in Postgres
    models.Base.metadata.create_all(bind=pg_engine)
    
    db_sqlite = SessionLocalSqlite()
    db_pg = SessionLocalPg()
    
    try:
        # 1. Migrate Users
        users = db_sqlite.query(models.User).all()
        inserted_users = 0
        for u in users:
            if not db_pg.query(models.User).filter_by(id=u.id).first():
                db_pg.add(models.User(
                    id=u.id, email=u.email, google_id=u.google_id,
                    password_hash=u.password_hash, dominant_color=u.dominant_color,
                    secondary_color=u.secondary_color, color_scores=u.color_scores,
                    answer_vector=u.answer_vector, display_name=u.display_name,
                    avatar_url=u.avatar_url, created_at=u.created_at, updated_at=u.updated_at
                ))
                inserted_users += 1
        
        # 2. Migrate QuizResponse
        responses = db_sqlite.query(models.QuizResponse).all()
        inserted_responses = 0
        for r in responses:
            if not db_pg.query(models.QuizResponse).filter_by(id=r.id).first():
                db_pg.add(models.QuizResponse(
                    id=r.id, session_id=r.session_id, answers=r.answers,
                    color_scores=r.color_scores, dominant_color=r.dominant_color,
                    secondary_color=r.secondary_color, created_at=r.created_at
                ))
                inserted_responses += 1
                
        # 3. Migrate ContactSubmission
        submissions = db_sqlite.query(models.ContactSubmission).all()
        inserted_submissions = 0
        for s in submissions:
            if not db_pg.query(models.ContactSubmission).filter_by(id=s.id).first():
                db_pg.add(models.ContactSubmission(
                    id=s.id, name=s.name, email=s.email, message=s.message,
                    created_at=s.created_at
                ))
                inserted_submissions += 1
                
        # 4. Migrate ModelMeta
        metas = db_sqlite.query(models.ModelMeta).all()
        inserted_metas = 0
        for m in metas:
            if not db_pg.query(models.ModelMeta).filter_by(id=m.id).first():
                db_pg.add(models.ModelMeta(
                    id=m.id, version=m.version, model_type=m.model_type,
                    accuracy=m.accuracy, sample_count=m.sample_count,
                    trained_at=m.trained_at
                ))
                inserted_metas += 1
        
        db_pg.commit()
        
        # Advance PostgreSQL ID sequences so it doesn't crash on new inserts
        tables = ["users", "quiz_responses", "contact_submissions", "model_meta"]
        for table in tables:
            db_pg.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1) + 1);"))
        db_pg.commit()
        
        print("\n--- Migration Summary ---")
        print(f"Users migrated: {inserted_users}/{len(users)}")
        print(f"Responses migrated: {inserted_responses}/{len(responses)}")
        print(f"Contact Submissions migrated: {inserted_submissions}/{len(submissions)}")
        print(f"Model Metas migrated: {inserted_metas}/{len(metas)}")
        print("-------------------------\nMigration Completed Successfully!")
        
    except Exception as e:
        print(f"Migration Failed: {e}")
        db_pg.rollback()
    finally:
        db_sqlite.close()
        db_pg.close()

if __name__ == "__main__":
    migrate()
