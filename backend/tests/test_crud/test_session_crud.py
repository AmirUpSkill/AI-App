import pytest
import uuid
from sqlalchemy.orm import Session

from app.crud.crud_session import crud_session
from app.models.session import Session as SessionModel
from app.models.message import Message, MessageRole
from app.schemas.session import SessionCreate, SessionUpdate


class TestCRUDSession:
    """
    Comprehensive tests for Session CRUD operations.
    Tests cover all basic CRUD operations plus session-specific methods.
    """

    def test_create_session(self, db: Session):
        """Test creating a new session."""
        session_data = SessionCreate(title="Test Session")
        session = crud_session.create(db=db, obj_in=session_data)
        
        assert session.title == "Test Session"
        assert session.id is not None
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_get_session_by_id(self, db: Session, sample_session: SessionModel):
        """Test retrieving a session by ID."""
        retrieved_session = crud_session.get(db=db, id=sample_session.id)
        
        assert retrieved_session is not None
        assert retrieved_session.id == sample_session.id
        assert retrieved_session.title == sample_session.title

    def test_get_nonexistent_session(self, db: Session):
        """Test retrieving a non-existent session returns None."""
        fake_id = uuid.uuid4()
        retrieved_session = crud_session.get(db=db, id=fake_id)
        
        assert retrieved_session is None

    def test_get_all_sessions(self, db: Session, multiple_sessions: list[SessionModel]):
        """Test retrieving all sessions."""
        sessions = crud_session.get_all_sessions(db=db)
        
        assert len(sessions) == 4
        # Verify they're ordered by updated_at (most recent first)
        session_titles = [s.title for s in sessions]
        assert "Docker Tutorial" in session_titles
        assert "FastAPI Best Practices" in session_titles

    def test_get_multi_sessions_with_pagination(self, db: Session, multiple_sessions: list[SessionModel]):
        """Test retrieving sessions with pagination."""
        # Get first 2 sessions
        sessions_page_1 = crud_session.get_multi(db=db, skip=0, limit=2)
        assert len(sessions_page_1) == 2
        
        # Get next 2 sessions
        sessions_page_2 = crud_session.get_multi(db=db, skip=2, limit=2)
        assert len(sessions_page_2) == 2
        
        # Verify no overlap
        page_1_ids = {s.id for s in sessions_page_1}
        page_2_ids = {s.id for s in sessions_page_2}
        assert page_1_ids.isdisjoint(page_2_ids)

    def test_update_session_title(self, db: Session, sample_session: SessionModel):
        """Test updating a session's title."""
        original_title = sample_session.title
        update_data = SessionUpdate(title="Updated Session Title")
        
        updated_session = crud_session.update(
            db=db, 
            db_obj=sample_session, 
            obj_in=update_data
        )
        
        assert updated_session.title == "Updated Session Title"
        assert updated_session.title != original_title
        assert updated_session.id == sample_session.id

    def test_update_session_with_dict(self, db: Session, sample_session: SessionModel):
        """Test updating a session using a dictionary."""
        updated_session = crud_session.update(
            db=db,
            db_obj=sample_session,
            obj_in={"title": "Dict Updated Title"}
        )
        
        assert updated_session.title == "Dict Updated Title"

    def test_delete_session(self, db: Session, sample_session: SessionModel):
        """Test deleting a session."""
        session_id = sample_session.id
        
        deleted_session = crud_session.remove(db=db, id=session_id)
        
        assert deleted_session is not None
        assert deleted_session.id == session_id
        
        # Verify it's actually deleted
        retrieved_session = crud_session.get(db=db, id=session_id)
        assert retrieved_session is None

    def test_delete_nonexistent_session(self, db: Session):
        """Test deleting a non-existent session returns None."""
        fake_id = uuid.uuid4()
        deleted_session = crud_session.remove(db=db, id=fake_id)
        
        assert deleted_session is None

    def test_search_sessions_by_title(self, db: Session, multiple_sessions: list[SessionModel]):
        """Test searching sessions by title keyword."""
        # Search for sessions containing "Docker"
        docker_sessions = crud_session.search_by_title(db=db, keyword="Docker")
        
        assert len(docker_sessions) == 2  # "Docker Tutorial" and "Docker Compose Setup"
        session_titles = [s.title for s in docker_sessions]
        assert "Docker Tutorial" in session_titles
        assert "Docker Compose Setup" in session_titles

    def test_search_sessions_case_insensitive(self, db: Session, multiple_sessions: list[SessionModel]):
        """Test that search is case-insensitive."""
        # Search with different cases
        upper_results = crud_session.search_by_title(db=db, keyword="FASTAPI")
        lower_results = crud_session.search_by_title(db=db, keyword="fastapi")
        mixed_results = crud_session.search_by_title(db=db, keyword="FastApi")
        
        # All should return the same result
        assert len(upper_results) == len(lower_results) == len(mixed_results) == 1
        assert upper_results[0].title == "FastAPI Best Practices"

    def test_search_sessions_no_results(self, db: Session, multiple_sessions: list[SessionModel]):
        """Test searching with a keyword that matches no sessions."""
        results = crud_session.search_by_title(db=db, keyword="NonexistentKeyword")
        
        assert len(results) == 0

    def test_session_cascade_delete_with_messages(self, db: Session, sample_session_with_messages: SessionModel):
        """Test that deleting a session also deletes its messages (cascade)."""
        session_id = sample_session_with_messages.id
        
        # Verify messages exist before deletion
        messages_before = db.query(Message).filter(Message.session_id == session_id).all()
        assert len(messages_before) == 2
        
        # Delete the session
        crud_session.remove(db=db, id=session_id)
        
        # Verify messages are also deleted
        messages_after = db.query(Message).filter(Message.session_id == session_id).all()
        assert len(messages_after) == 0

    def test_session_relationship_with_messages(self, db: Session, sample_session_with_messages: SessionModel):
        """Test that session relationships with messages work correctly."""
        # Refresh to load relationships
        db.refresh(sample_session_with_messages)
        
        assert len(sample_session_with_messages.messages) == 2
        
        # Check message roles
        message_roles = [msg.role for msg in sample_session_with_messages.messages]
        assert MessageRole.USER in message_roles
        assert MessageRole.AI in message_roles

    def test_create_multiple_sessions_concurrent(self, db: Session):
        """Test creating multiple sessions doesn't cause conflicts."""
        session_data_list = [
            SessionCreate(title=f"Concurrent Session {i}")
            for i in range(5)
        ]
        
        created_sessions = []
        for session_data in session_data_list:
            session = crud_session.create(db=db, obj_in=session_data)
            created_sessions.append(session)
        
        # Verify all sessions were created with unique IDs
        assert len(created_sessions) == 5
        session_ids = {s.id for s in created_sessions}
        assert len(session_ids) == 5  # All IDs are unique

    def test_empty_database_operations(self, db: Session):
        """Test operations on an empty database."""
        # Test get_all_sessions on empty database
        sessions = crud_session.get_all_sessions(db=db)
        assert len(sessions) == 0
        
        # Test search on empty database
        results = crud_session.search_by_title(db=db, keyword="anything")
        assert len(results) == 0
        
        # Test pagination on empty database
        paginated = crud_session.get_multi(db=db, skip=0, limit=10)
        assert len(paginated) == 0
