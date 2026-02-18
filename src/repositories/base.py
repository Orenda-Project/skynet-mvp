"""
Base repository class with common CRUD operations.
Follows Guardrail #2: Repository Pattern (database abstraction)
"""

from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from src.models.base import BaseModel


ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common database operations.
    All repositories inherit from this to get standard CRUD methods.

    Following the Repository Pattern ensures:
    - Services never touch the database directly
    - Easy to mock for testing
    - Database can be swapped without changing service code
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session (injected)
        """
        self.model = model
        self.db = db

    def create(self, **kwargs) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record ID (UUID string)

        Returns:
            Model instance or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """
        Update a record.

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        instance = self.get_by_id(id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, id: str) -> bool:
        """
        Delete a record.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if not instance:
            return False

        self.db.delete(instance)
        self.db.commit()
        return True

    def count(self) -> int:
        """
        Count total records.

        Returns:
            Total number of records
        """
        return self.db.query(self.model).count()

    def exists(self, id: str) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).count() > 0
