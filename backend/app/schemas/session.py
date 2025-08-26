import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .message import Message

# --- Core Session Schemas ---

class SessionBase(BaseModel):
    """
    Base schema for a session, containing only the title.
    """
    title: str

class SessionCreate(SessionBase):
    """
    Schema used for creating a new session internally.
    """
    pass

class SessionUpdate(BaseModel):
    """
    Schema for the request body when updating a session's title.
    """
    title: str

class Session(SessionBase):
    """
    Schema for a single session item in a list (e.g., in the Conversation Hub).
    """
    id: uuid.UUID

    class Config:
        from_attributes = True

# --- API Endpoint Specific DTOs ---

class ChatRequest(BaseModel):
    """
    Schema for the POST /chat request body.
    """
    prompt: str
    sessionId: Optional[uuid.UUID] = None

class ChatResponse(BaseModel):
    """
    Schema for the POST /chat response body.
    """
    ai_response: str
    sessionId: uuid.UUID
    sessionTitle: str

class SessionHistory(SessionBase):
    """
    Schema for the GET /sessions/{sessionId} response.
    Includes the full chat history.
    """
    id: uuid.UUID
    chat_history: List[Message]

    class Config:
        from_attributes = True

class AllSessionsResponse(BaseModel):
    """
    Schema for the GET /sessions response, grouping sessions by time.
    """
    Today: List[Session]
    Yesterday: List[Session]
    Previous_30_Days: List[Session] = Field(..., alias="Previous 30 Days")
