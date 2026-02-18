"""initial schema - conversations, participants, syntheses

Revision ID: 001_initial
Revises:
Create Date: 2026-01-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'TRANSCRIBING', 'SYNTHESIZING', 'COMPLETED', 'FAILED', name='conversationstatus'), nullable=False, index=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('platform_meeting_id', sa.String(255), nullable=True, index=True),
        sa.Column('meeting_url', sa.String(512), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('transcript_word_count', sa.Integer(), nullable=True),
        sa.Column('transcription_provider', sa.String(50), nullable=True),
        sa.Column('synthesis_provider', sa.String(50), nullable=True),
        sa.Column('processing_time_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )

    # Create participants table
    op.create_table(
        'participants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('is_organizer', sa.Boolean(), nullable=False, default=False),
        sa.Column('conversation_id', sa.String(36), nullable=False, index=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )

    # Create syntheses table
    op.create_table(
        'syntheses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=False, unique=True, index=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('summary_word_count', sa.Integer(), nullable=True),
        sa.Column('key_decisions', sa.JSON(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('open_questions', sa.JSON(), nullable=True),
        sa.Column('key_topics', sa.JSON(), nullable=True),
        sa.Column('llm_model', sa.String(50), nullable=True),
        sa.Column('llm_tokens_used', sa.Integer(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('email_sent_at', sa.String(255), nullable=True),
        sa.Column('email_recipients', sa.JSON(), nullable=True),
        sa.Column('email_delivery_status', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('syntheses')
    op.drop_table('participants')
    op.drop_table('conversations')
    op.execute('DROP TYPE conversationstatus')
