from typing import List, Union
import uuid
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

from .base import CRUDBase
from app.models.session import Session as SessionModel
from app.models.message import Message, MessageRole
from app.schemas.session import SessionCreate, SessionUpdate
from app.schemas.message import MessageCreate

class CRUDSession(CRUDBase[SessionModel, SessionCreate, SessionUpdate]):
    """
    CRUD methods for Session model, with specific helper functions.
    """
    def get_all_sessions(self, db: DBSession) -> List[SessionModel]:
        """
        Retrieves all sessions, ordered by the most recently updated.
        """
        return db.query(self.model).order_by(desc(self.model.updated_at)).all()

    def search_by_title(self, db: DBSession, *, keyword: str) -> List[SessionModel]:
        """
        Searches for sessions with a title containing the keyword (case-insensitive).
        """
        return db.query(self.model).filter(self.model.title.ilike(f"%{keyword}%")).order_by(desc(self.model.updated_at)).all()

# Create a simple update schema for Message (since we don't have complex updates)
class MessageUpdate(MessageCreate):
    pass

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]): 
    """
    CRUD methods for Message model.
    """
    def create_with_session(
        self, db: DBSession, *, obj_in: MessageCreate, session_id: Union[str, uuid.UUID]
    ) -> Message:
        """
        Creates a new message and associates it with a session.
        """
        # Convert string to UUID if necessary
        if isinstance(session_id, str):
            session_id = uuid.UUID(session_id)
        
        db_obj = self.model(**obj_in.model_dump(), session_id=session_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_session(self, db: DBSession, *, session_id: Union[str, uuid.UUID]) -> List[Message]:
        """
        Retrieves all messages for a given session, ordered by creation time.
        """
        # Convert string to UUID if necessary
        if isinstance(session_id, str):
            session_id = uuid.UUID(session_id)
        
        return db.query(self.model).filter(
            self.model.session_id == session_id
        ).order_by(self.model.created_at).all()

crud_session = CRUDSession(SessionModel)
crud_message = CRUDMessage(Message)
