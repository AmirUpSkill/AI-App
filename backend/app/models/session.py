import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

class Session(Base):
    """
        Represents a chat session in the database .
    Each session has a unique ID , a title  and creation/update timestamps .    
        
    """
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # --- One-To-Many relationship with the Message Model --- 
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
    )