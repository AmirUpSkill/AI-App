from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .base import CRUDBase
from app.models.session import Session
from app.models.message import Message, MessageRole
from app.schemas.session import SessionCreate, SessionUpdate
from app.schemas.message import MessageCreate

class CRUDSession(CRUDBase[Session, SessionCreate, SessionUpdate]):
    """
    CRUD methods for Session model, with specific helper functions.
    """
    def get_all_sessions(self, db: Session) -> List[Session]:
        """
        Retrieves all sessions, ordered by the most recently updated.
        """
        return db.query(self.model).order_by(desc(self.model.updated_at)).all()

    def search_by_title(self, db: Session, *, keyword: str) -> List[Session]:
        """
        Searches for sessions with a title containing the keyword (case-insensitive).
        """
        return db.query(self.model).filter(self.model.title.ilike(f"%{keyword}%")).order_by(desc(self.model.updated_at)).all()

class CRUDMessage(CRUDBase[Message, MessageCreate, SessionUpdate]): 
    """
    CRUD methods for Message model.
    """
    def create_with_session(
        self, db: Session, *, obj_in: MessageCreate, session_id: str
    ) -> Message:
        """
        Creates a new message and associates it with a session.
        """
        db_obj = self.model(**obj_in.model_dump(), session_id=session_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_session = CRUDSession(Session)
crud_message = CRUDMessage(Message)