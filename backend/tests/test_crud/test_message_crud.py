import pytest
import uuid
from sqlalchemy.orm import Session

from app.crud.crud_session import crud_message
from app.models.session import Session as SessionModel
from app.models.message import Message, MessageRole
from app.schemas.message import MessageCreate


class TestCRUDMessage:
    """
    Comprehensive tests for Message CRUD operations.
    Tests cover basic CRUD operations and message-specific methods.
    """

    def test_create_message(self, db: Session, sample_session: SessionModel):
        """Test creating a new message."""
        message_data = MessageCreate(
            role=MessageRole.USER,
            content="Hello, this is a test message"
        )
        
        message = crud_message.create_with_session(
            db=db,
            obj_in=message_data,
            session_id=str(sample_session.id)
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Hello, this is a test message"
        assert message.session_id == sample_session.id
        assert message.id is not None
        assert message.created_at is not None

    def test_create_ai_message(self, db: Session, sample_session: SessionModel):
        """Test creating an AI message."""
        message_data = MessageCreate(
            role=MessageRole.AI,
            content="This is an AI response"
        )
        
        message = crud_message.create_with_session(
            db=db,
            obj_in=message_data,
            session_id=str(sample_session.id)
        )
        
        assert message.role == MessageRole.AI
        assert message.content == "This is an AI response"
        assert message.session_id == sample_session.id

    def test_get_message_by_id(self, db: Session, sample_session_with_messages: SessionModel):
        """Test retrieving a message by ID."""
        # Get the first message from the session
        first_message = sample_session_with_messages.messages[0]
        
        retrieved_message = crud_message.get(db=db, id=first_message.id)
        
        assert retrieved_message is not None
        assert retrieved_message.id == first_message.id
        assert retrieved_message.content == first_message.content
        assert retrieved_message.role == first_message.role

    def test_get_nonexistent_message(self, db: Session):
        """Test retrieving a non-existent message returns None."""
        fake_id = uuid.uuid4()
        retrieved_message = crud_message.get(db=db, id=fake_id)
        
        assert retrieved_message is None

    def test_get_multiple_messages_with_pagination(self, db: Session, sample_session: SessionModel):
        """Test retrieving messages with pagination."""
        # Create multiple messages
        for i in range(5):
            message_data = MessageCreate(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.AI,
                content=f"Message {i}"
            )
            crud_message.create_with_session(
                db=db,
                obj_in=message_data,
                session_id=str(sample_session.id)
            )
        
        # Test pagination
        first_page = crud_message.get_multi(db=db, skip=0, limit=3)
        assert len(first_page) == 3
        
        second_page = crud_message.get_multi(db=db, skip=3, limit=3)
        assert len(second_page) == 2  # Only 2 remaining messages
        
        # Verify no overlap
        first_page_ids = {m.id for m in first_page}
        second_page_ids = {m.id for m in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)

    def test_delete_message(self, db: Session, sample_session_with_messages: SessionModel):
        """Test deleting a message."""
        message_to_delete = sample_session_with_messages.messages[0]
        message_id = message_to_delete.id
        
        deleted_message = crud_message.remove(db=db, id=message_id)
        
        assert deleted_message is not None
        assert deleted_message.id == message_id
        
        # Verify it's actually deleted
        retrieved_message = crud_message.get(db=db, id=message_id)
        assert retrieved_message is None

    def test_delete_nonexistent_message(self, db: Session):
        """Test deleting a non-existent message returns None."""
        fake_id = uuid.uuid4()
        deleted_message = crud_message.remove(db=db, id=fake_id)
        
        assert deleted_message is None

    def test_message_session_relationship(self, db: Session, sample_session_with_messages: SessionModel):
        """Test that message-session relationships work correctly."""
        message = sample_session_with_messages.messages[0]
        
        # Access the session through the relationship
        assert message.session.id == sample_session_with_messages.id
        assert message.session.title == sample_session_with_messages.title

    def test_create_message_with_invalid_session(self, db: Session):
        """Test creating a message with non-existent session ID."""
        fake_session_id = str(uuid.uuid4())
        message_data = MessageCreate(
            role=MessageRole.USER,
            content="This should fail"
        )
        
        # In SQLite, FK constraints aren't enforced by default, so this will create the message
        # In production with PostgreSQL, this would fail
        message = crud_message.create_with_session(
            db=db,
            obj_in=message_data,
            session_id=fake_session_id
        )
        
        # Verify the message was created but with orphaned session_id
        assert message.session_id == uuid.UUID(fake_session_id)
        assert message.session is None  # No actual session exists

    def test_create_conversation_flow(self, db: Session, sample_session: SessionModel):
        """Test creating a realistic conversation flow."""
        # User asks a question
        user_message_data = MessageCreate(
            role=MessageRole.USER,
            content="What is FastAPI?"
        )
        user_message = crud_message.create_with_session(
            db=db,
            obj_in=user_message_data,
            session_id=str(sample_session.id)
        )
        
        # AI responds
        ai_message_data = MessageCreate(
            role=MessageRole.AI,
            content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints."
        )
        ai_message = crud_message.create_with_session(
            db=db,
            obj_in=ai_message_data,
            session_id=str(sample_session.id)
        )
        
        # Verify both messages exist and are linked to the session
        all_messages = db.query(Message).filter(Message.session_id == sample_session.id).all()
        assert len(all_messages) == 2
        
        # Verify order (user message should be created before AI message)
        user_msg = next(msg for msg in all_messages if msg.role == MessageRole.USER)
        ai_msg = next(msg for msg in all_messages if msg.role == MessageRole.AI)
        
        assert user_msg.created_at <= ai_msg.created_at

    def test_long_message_content(self, db: Session, sample_session: SessionModel):
        """Test creating messages with long content."""
        long_content = "This is a very long message. " * 100  # 2900+ characters
        
        message_data = MessageCreate(
            role=MessageRole.AI,
            content=long_content
        )
        
        message = crud_message.create_with_session(
            db=db,
            obj_in=message_data,
            session_id=str(sample_session.id)
        )
        
        assert message.content == long_content
        assert len(message.content) > 2000

    def test_message_role_validation(self, db: Session, sample_session: SessionModel):
        """Test that message roles are correctly validated."""
        # Test USER role
        user_message_data = MessageCreate(
            role=MessageRole.USER,
            content="User message"
        )
        user_message = crud_message.create_with_session(
            db=db,
            obj_in=user_message_data,
            session_id=str(sample_session.id)
        )
        assert user_message.role == MessageRole.USER
        
        # Test AI role
        ai_message_data = MessageCreate(
            role=MessageRole.AI,
            content="AI message"
        )
        ai_message = crud_message.create_with_session(
            db=db,
            obj_in=ai_message_data,
            session_id=str(sample_session.id)
        )
        assert ai_message.role == MessageRole.AI

    def test_multiple_messages_same_session(self, db: Session, sample_session: SessionModel):
        """Test creating multiple messages in the same session."""
        messages_to_create = 10
        
        for i in range(messages_to_create):
            message_data = MessageCreate(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.AI,
                content=f"Message number {i + 1}"
            )
            crud_message.create_with_session(
                db=db,
                obj_in=message_data,
                session_id=str(sample_session.id)
            )
        
        # Verify all messages were created
        all_messages = db.query(Message).filter(Message.session_id == sample_session.id).all()
        assert len(all_messages) == messages_to_create
        
        # Verify they all belong to the same session
        session_ids = {msg.session_id for msg in all_messages}
        assert len(session_ids) == 1
        assert list(session_ids)[0] == sample_session.id

    def test_empty_message_content(self, db: Session, sample_session: SessionModel):
        """Test creating a message with empty content."""
        message_data = MessageCreate(
            role=MessageRole.USER,
            content=""
        )
        
        message = crud_message.create_with_session(
            db=db,
            obj_in=message_data,
            session_id=str(sample_session.id)
        )
        
        assert message.content == ""
        assert message.role == MessageRole.USER
