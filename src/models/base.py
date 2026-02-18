"""
Base model class with common fields and utilities.
All database models inherit from this.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from uuid import uuid4

from src.database.postgres import Base


class BaseModel(Base):
    """
    Abstract base model with common fields and utilities.
    All models inherit from this to get:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    - Common utility methods
    """

    __abstract__ = True  # Don't create a table for this class

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Automatically generate table name from class name.
        Example: ConversationModel -> conversations
        """
        return cls.__name__.lower() + "s"

    # Primary key (UUID for better distribution and security)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Timestamps (automatically managed)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary.
        Useful for serialization to JSON.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(id={self.id})>"
