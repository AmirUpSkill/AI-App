import uuid
from typing import Generator, Dict, List, Optional, Any
from datetime import datetime, timedelta
import ollama
from ollama import ResponseError
from sqlalchemy.orm import Session as DBSession

from app.crud.crud_session import crud_session, crud_message
from app.schemas.session import ChatRequest, ChatResponse, AllSessionsResponse, Session as SessionSchema, SessionCreate
from app.schemas.message import MessageCreate
from app.models.message import MessageRole, Message
from app.models.session import Session as SessionModel
from app.db.session import SessionLocal

PREVIOUS_30_DAYS = "Previous 30 Days"

class ChatService:
    """
    Service layer for handling chat operations, integrating CRUD with AI model.
    Orchestrates business logic for sessions and messages.
    """

    def __init__(
        self,
        session_crud=crud_session,
        message_crud=crud_message,
        ollama_model: str = "gemma:2b",
    ):
        """
        Initialize with injected dependencies.
        - session_crud: CRUD for sessions
        - message_crud: CRUD for messages
        - ollama_model: Model name for Ollama
        """
        self.session_crud = session_crud
        self.message_crud = message_crud
        self.ollama_model = ollama_model

    def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Main entry point for processing chat requests.
        Handles both new and existing sessions.
        Returns full response after streaming and saving.
        """
        db = SessionLocal()  # Create DB session
        try:
            if request.sessionId is None:
                # Create new session
                temp_title = "New Conversation"
                new_session = self.session_crud.create(db, obj_in=SessionCreate(title=temp_title))
                session = new_session
            else:
                # Get existing session
                session = self.session_crud.get(db, id=request.sessionId)
                if not session:
                    raise ValueError(f"Session {request.sessionId} not found")

            # Extract actual values from the session object
            session_id = session.id
            session_title = session.title

            # Save user message
            user_msg = MessageCreate(role=MessageRole.USER, content=request.prompt)
            self.message_crud.create_with_session(db, obj_in=user_msg, session_id=str(session_id))

            # Get full history for AI context
            history = self._build_ollama_history(self._get_chat_history(db, session_id))

            # Generate AI response via streaming, but collect full content
            full_ai_response = ""
            for chunk in self.stream_ai_response(history):
                full_ai_response += chunk.get("chunk", "")

            # Save AI message
            ai_msg = MessageCreate(role=MessageRole.AI, content=full_ai_response)
            self.message_crud.create_with_session(db, obj_in=ai_msg, session_id=str(session_id))

            # If new session, generate and update title
            if request.sessionId is None:
                generated_title = self.generate_session_title(request.prompt)
                self.session_crud.update(db, db_obj=session, obj_in={"title": generated_title})
                session_title = generated_title

            # Update session timestamp
            self.session_crud.update(db, db_obj=session, obj_in={})  # Triggers onupdate

            return ChatResponse(
                ai_response=full_ai_response,
                sessionId=uuid.UUID(str(session_id)),
                sessionTitle=str(session_title)
            )
        except ResponseError as e:
            raise RuntimeError(f"Ollama error: {e.error}") from e
        except Exception as e:
            raise RuntimeError(f"Service error: {str(e)}") from e
        finally:
            db.close()

    def stream_ai_response(self, history: List[Dict[str, str]]) -> Generator[Dict[str, str], None, None]:
        """
        Generate streaming response from AI.
        Yields chunks in SSE-friendly format.
        """
        try:
            stream = ollama.chat(
                model=self.ollama_model,
                messages=history,
                stream=True
            )
            for part in stream:
                content = part.get('message', {}).get('content', '')
                if content:
                    yield {"chunk": content}
        except ResponseError as e:
            yield {"error": f"Ollama streaming error: {e.error}"}

    def generate_session_title(self, prompt: str) -> str:
        """
        Generate concise title from first prompt using AI.
        """
        title_prompt = f"Summarize this prompt in 3-5 words: {prompt}"
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": title_prompt}]
            )
            return response['message']['content'].strip()
        except ResponseError:
            return "Untitled Conversation" 

    def get_sessions_grouped_by_time(self, query: Optional[str] = None) -> Dict[str, List[SessionSchema]]:
        """
        Get all sessions grouped by relative time periods.
        Supports optional search query.
        Returns dict for API to validate and serialize.
        """
        db = SessionLocal()
        try:
            if query:
                all_sessions = self.session_crud.search_by_title(db, keyword=query)
            else:
                all_sessions = self.session_crud.get_all_sessions(db)

            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            thirty_days_ago = today - timedelta(days=30)

            grouped: Dict[str, List[SessionSchema]] = {
                "Today": [],
                "Yesterday": [],
                PREVIOUS_30_DAYS: []
            }

            for sess in all_sessions:
                sess_date = sess.created_at.date()
                # Extract actual values from the session object
                sess_id = sess.id
                sess_title = sess.title
                session_data = SessionSchema(id=uuid.UUID(str(sess_id)), title=str(sess_title))
                if sess_date == today:
                    grouped["Today"].append(session_data)
                elif sess_date == yesterday:
                    grouped["Yesterday"].append(session_data)
                elif thirty_days_ago <= sess_date < yesterday:
                    grouped[PREVIOUS_30_DAYS].append(session_data)

            return grouped
        finally:
            db.close()

    def _get_chat_history(self, db: DBSession, session_id) -> List[Message]:
        """
        Internal: Get ordered message history for a session.
        """
        return self.message_crud.get_by_session(db, session_id=session_id)

    def _build_ollama_history(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Internal: Format DB messages to Ollama's expected format.
        """
        return [
            {"role": msg.role.value, "content": str(msg.content)}
            for msg in messages
        ]
