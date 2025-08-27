from typing import Generator
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

app = FastAPI(
    title="FocusFlow API",
    description="A modern conversational AI interface",
    version="1.0.0"
)

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency that provides a SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}
