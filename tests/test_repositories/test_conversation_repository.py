"""
Tests for ConversationRepository.
Tests database operations using an in-memory SQLite database.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.postgres import Base
from src.models.conversation import Conversation, ConversationStatus
from src.repositories.conversation_repository import ConversationRepository


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def conversation_repo(test_db):
    """Create ConversationRepository with test database."""
    return ConversationRepository(test_db)


def test_create_conversation(conversation_repo):
    """Test creating a new conversation."""
    conversation = conversation_repo.create(
        title="Test Meeting",
        status=ConversationStatus.PENDING,
        platform="zoom"
    )

    assert conversation.id is not None
    assert conversation.title == "Test Meeting"
    assert conversation.status == ConversationStatus.PENDING
    assert conversation.platform == "zoom"


def test_get_by_id(conversation_repo):
    """Test retrieving conversation by ID."""
    # Create a conversation
    created = conversation_repo.create(
        title="Test Meeting",
        status=ConversationStatus.PENDING
    )

    # Retrieve it
    retrieved = conversation_repo.get_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.title == "Test Meeting"


def test_get_by_id_not_found(conversation_repo):
    """Test retrieving non-existent conversation returns None."""
    result = conversation_repo.get_by_id("nonexistent-id")
    assert result is None


def test_get_by_status(conversation_repo):
    """Test retrieving conversations by status."""
    # Create conversations with different statuses
    conversation_repo.create(title="Pending 1", status=ConversationStatus.PENDING)
    conversation_repo.create(title="Pending 2", status=ConversationStatus.PENDING)
    conversation_repo.create(title="Completed", status=ConversationStatus.COMPLETED)

    # Get pending conversations
    pending = conversation_repo.get_by_status(ConversationStatus.PENDING)

    assert len(pending) == 2
    assert all(c.status == ConversationStatus.PENDING for c in pending)


def test_search_by_title(conversation_repo):
    """Test searching conversations by title."""
    conversation_repo.create(title="Product Planning Meeting")
    conversation_repo.create(title="Engineering Standup")
    conversation_repo.create(title="Product Review")

    # Search for "product"
    results = conversation_repo.search_by_title("product")

    assert len(results) == 2
    assert all("product" in c.title.lower() for c in results)


def test_update_conversation(conversation_repo):
    """Test updating a conversation."""
    # Create conversation
    conversation = conversation_repo.create(
        title="Original Title",
        status=ConversationStatus.PENDING
    )

    # Update it
    updated = conversation_repo.update(
        conversation.id,
        title="Updated Title",
        status=ConversationStatus.COMPLETED
    )

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.status == ConversationStatus.COMPLETED


def test_delete_conversation(conversation_repo):
    """Test deleting a conversation."""
    # Create conversation
    conversation = conversation_repo.create(title="To Be Deleted")

    # Delete it
    result = conversation_repo.delete(conversation.id)
    assert result is True

    # Verify it's gone
    retrieved = conversation_repo.get_by_id(conversation.id)
    assert retrieved is None


def test_count(conversation_repo):
    """Test counting conversations."""
    assert conversation_repo.count() == 0

    conversation_repo.create(title="Meeting 1")
    conversation_repo.create(title="Meeting 2")
    conversation_repo.create(title="Meeting 3")

    assert conversation_repo.count() == 3
