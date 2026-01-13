"""add_agent_type_for_subagent_isolation

Revision ID: 0003_add_agent_type
Revises: 62723bb6eea9
Create Date: 2026-01-13

This migration adds agent_type columns to conversations and chat_logs tables
to ensure proper memory separation between Patient Concierge and Clinical Advisor.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_agent_type'
down_revision: Union[str, Sequence[str], None] = '62723bb6eea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agent_type column to conversations and chat_logs for subagent isolation."""

    # 1. Add agent_type column to conversations table
    # Default to 'patient' for existing conversations (Patient Concierge is the primary use case)
    op.add_column(
        'conversations',
        sa.Column('agent_type', sa.String(20), nullable=False, server_default='patient')
    )
    
    # Add index for better query performance when filtering by agent_type
    op.create_index('ix_conversations_agent_type', 'conversations', ['agent_type'])

    # 2. Add agent_type column to chat_logs table
    # Default to 'patient' for existing chat logs
    op.add_column(
        'chat_logs',
        sa.Column('agent_type', sa.String(20), nullable=False, server_default='patient')
    )
    
    # Add index for better query performance when filtering by agent_type
    op.create_index('ix_chat_logs_agent_type', 'chat_logs', ['agent_type'])


def downgrade() -> None:
    """Remove agent_type columns from conversations and chat_logs."""

    # Remove indexes first
    op.drop_index('ix_chat_logs_agent_type', table_name='chat_logs')
    op.drop_index('ix_conversations_agent_type', table_name='conversations')
    
    # Remove columns
    op.drop_column('chat_logs', 'agent_type')
    op.drop_column('conversations', 'agent_type')
