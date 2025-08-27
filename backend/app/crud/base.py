from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Protocol
from pydantic import BaseModel
from sqlalchemy.orm import Session


class DBModel(Protocol):
    """Protocol defining the interface for database models."""
    id: Any


ModelType = TypeVar("ModelType", bound=DBModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base CRUD class with common database operations."""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Retrieve a single object by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """Retrieve multiple objects with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new object in the database."""
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing object in the database."""
        update_data = (
            obj_in if isinstance(obj_in, dict) 
            else obj_in.model_dump(exclude_unset=True)
        )
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """Remove an object from the database by ID."""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
