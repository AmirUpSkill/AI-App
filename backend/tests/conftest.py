import pytest
import uuid
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import SessionLocal
# from app.main import app  # We'll import this conditionally
from app.models.session import Session as SessionModel
from app.models.message import Message, MessageRole

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    This fixture ensures test isolation by creating and dropping tables.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=engine)

# Client fixture removed - we'll focus on CRUD testing only

@pytest.fixture
def sample_session(db: Session) -> SessionModel:
    """
    Create a sample session for testing.
    """
    session = SessionModel(
        title="Test Session",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@pytest.fixture
def sample_session_with_messages(db: Session) -> SessionModel:
    """
    Create a sample session with messages for testing.
    """
    session = SessionModel(
        title="Session with Messages",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Add user message
    user_message = Message(
        session_id=session.id,
        role=MessageRole.USER,
        content="Hello, how are you?"
    )
    db.add(user_message)
    
    # Add AI message
    ai_message = Message(
        session_id=session.id,
        role=MessageRole.AI,
        content="I'm doing well, thank you for asking!"
    )
    db.add(ai_message)
    
    db.commit()
    return session

@pytest.fixture
def multiple_sessions(db: Session) -> list[SessionModel]:
    """
    Create multiple sessions for testing search and retrieval.
    """
    sessions = [
        SessionModel(title="Docker Tutorial"),
        SessionModel(title="FastAPI Best Practices"),
        SessionModel(title="Unit Testing Guide"),
        SessionModel(title="Docker Compose Setup")
    ]
    
    for session in sessions:
        db.add(session)
    
    db.commit()
    
    for session in sessions:
        db.refresh(session)
    
    return sessions
