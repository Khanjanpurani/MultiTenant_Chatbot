import datetime
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from src.models.models import Conversation, ChatLog, PracticeProfile
from src.services.data_export import simple_data_exporter

logger = logging.getLogger(__name__)

def simple_data_exporter(conversation: Conversation):
    """
    A simple placeholder for exporting finalized lead data.
    In a real system, this would send an email, post to a webhook, or save to a CRM.
    """
    log_data = {
        'conversation_id': str(conversation.conversation_id),
        'client_id': str(conversation.client_id),
        'finalized_at': conversation.finalized_at.isoformat(),
        'collected_data': conversation.conversation_state
    }
    logger.info("LEAD FINALIZED", extra=log_data)

def finalize_conversation(db: Session, conversation_id: str):
    """
    Flags a conversation as finalized, captures the timestamp, and triggers data export.
    """
    try:
        conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        
        if conversation and not conversation.is_finalized:
            logger.info(f"Conversation before finalize: {conversation.conversation_state}", extra={'conversation_id': conversation_id})
            conversation.is_finalized = True
            conversation.finalized_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"Finalizing conversation and exporting data...", extra={'conversation_id': conversation_id})
            simple_data_exporter(conversation)
            return True
    except Exception as e:
        logger.error(f"ERROR in finalize_conversation: {e}", extra={'conversation_id': conversation_id})
        db.rollback()
        return False

def load_or_create_conversation(db: Session, conversation_id: str, client_id: str, agent_type: str = 'patient'):
    conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    if not conversation:
        conversation = Conversation(
            conversation_id=conversation_id,
            client_id=client_id,
            current_stage='GREETING',
            conversation_state={
                'name': None, 
                'phone': None, 
                'email': None, 
                'service': None,
                'appointment_type': None,
                'last_visit': None,
                'preferred_date': None,
                'preferred_time': None
            },
            agent_type=agent_type
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation

def get_conversation_by_id(db: Session, conversation_id: str):
    """Get an existing conversation by ID without creating a new one."""
    return db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()

def save_state(db: Session, conversation_id: str, stage: str, state: dict):
    conversation = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    if conversation:
        logger.info(f"Saving state for conversation {conversation_id}: {state}", extra={'conversation_id': conversation_id})
        conversation.current_stage = stage
        conversation.conversation_state = state
        db.commit()
        logger.info(f"Saved state for conversation {conversation_id}", extra={'conversation_id': conversation_id})

def get_conversation_history(db: Session, conversation_id: str, limit: int = 10, agent_type: str = None):
    """
    Retrieve conversation history for a specific conversation.
    
    Args:
        db: Database session
        conversation_id: The conversation ID to retrieve history for
        limit: Maximum number of messages to retrieve (default: 10)
        agent_type: Filter by agent type ('patient' or 'clinical') for isolation.
                   SECURITY NOTE: Production endpoints MUST provide this parameter
                   to ensure proper subagent isolation. Only omit for debug/admin
                   endpoints that explicitly need to see all messages.
    
    Returns:
        List of LangChain messages (HumanMessage/AIMessage) in chronological order
    
    Security:
        - Patient Concierge API MUST pass agent_type='patient'
        - Clinical Advisor API MUST pass agent_type='clinical' (if logging is added)
        - Admin/debug endpoints MAY omit agent_type to retrieve all messages
    """
    query = db.query(ChatLog).filter(ChatLog.conversation_id == conversation_id)
    
    # Apply agent_type filter if specified for proper subagent isolation
    # SECURITY: When agent_type is None, ALL messages are returned regardless of agent.
    # This is intentional for debug/admin use cases only.
    if agent_type:
        query = query.filter(ChatLog.agent_type == agent_type)
    
    logs = query.order_by(ChatLog.created_at.desc()).limit(limit).all()
    history = []
    for log in reversed(logs): # reverse to get chronological order
        if log.sender_type == 'user':
            history.append(HumanMessage(content=log.message))
        else:
            history.append(AIMessage(content=log.message))
    return history

def log_message(db: Session, conversation_id: str, sender: str, message: str, agent_type: str = 'patient'):
    """
    Log a message in the chat_logs table.
    
    Args:
        db: Database session
        conversation_id: The conversation ID
        sender: 'user' or 'bot'
        message: The message content
        agent_type: 'patient' or 'clinical' for proper subagent isolation
    """
    log = ChatLog(
        conversation_id=conversation_id,
        sender_type=sender,
        message=message,
        agent_type=agent_type
    )
    db.add(log)
    db.commit()


# =============================================================================
# Practice Profile Functions (for Clinical Advisor)
# =============================================================================

def get_practice_profile(db: Session, client_id: UUID) -> Optional[dict]:
    """
    Load the practice profile JSON for a given client.

    This retrieves the "Brain" data that contains the doctor's clinical philosophy,
    treatment preferences, and other practice-specific information used by the
    Clinical Advisor agent.

    Args:
        db: Database session
        client_id: The UUID of the client whose profile to load

    Returns:
        The profile_json dict if found, None if no profile exists for this client
    """
    profile = db.query(PracticeProfile).filter(
        PracticeProfile.practice_id == client_id
    ).first()

    if not profile:
        logger.warning(f"No practice profile found for client: {client_id}")
        return None

    logger.info(f"Loaded practice profile for client: {client_id}")
    return profile.profile_json


def create_or_update_practice_profile(
    db: Session,
    client_id: UUID,
    profile_json: dict
) -> PracticeProfile:
    """
    Create or update the practice profile for a client.

    Args:
        db: Database session
        client_id: The UUID of the client
        profile_json: The practice profile data to store

    Returns:
        The created or updated PracticeProfile object
    """
    profile = db.query(PracticeProfile).filter(
        PracticeProfile.practice_id == client_id
    ).first()

    if profile:
        # Update existing profile
        profile.profile_json = profile_json
        profile.updated_at = datetime.datetime.utcnow()
        logger.info(f"Updated practice profile for client: {client_id}")
    else:
        # Create new profile
        profile = PracticeProfile(
            practice_id=client_id,
            profile_json=profile_json
        )
        db.add(profile)
        logger.info(f"Created practice profile for client: {client_id}")

    db.commit()
    db.refresh(profile)
    return profile


def delete_practice_profile(db: Session, client_id: UUID) -> bool:
    """
    Delete the practice profile for a client.

    Args:
        db: Database session
        client_id: The UUID of the client whose profile to delete

    Returns:
        True if a profile was deleted, False if no profile existed
    """
    profile = db.query(PracticeProfile).filter(
        PracticeProfile.practice_id == client_id
    ).first()

    if not profile:
        logger.warning(f"No practice profile to delete for client: {client_id}")
        return False

    db.delete(profile)
    db.commit()
    logger.info(f"Deleted practice profile for client: {client_id}")
    return True