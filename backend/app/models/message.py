import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base

# --- Enum for AI Chat Roles --- 
class MessageRole(enum.Enum):
    """
        Enumeration for the role of the message sender .
    """
    USER = "user"
    AI = "ai"
class Message(Base):
    """
        Represents a single message within a chat session . 
    Each message has a unique ID , content , a role (user or AI) . and a timestamp . It is linked 
    to a parent session 
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    role = Column(SQLAlchemyEnum(MessageRole), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    # --- Many-to-one relationship with the session Model --- 
    session = relationship(
        "Session",
        back_populates="messages",
    )