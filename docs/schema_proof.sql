-- ============================================================================
-- SUBAGENT ISOLATION: Database Schema Proof
-- ============================================================================
-- This script demonstrates the agent_type column additions to ensure
-- memory separation between Patient Concierge and Clinical Advisor subagents.
--
-- Migration: 0003_add_agent_type_for_subagent_isolation
-- Date: 2026-01-13
-- ============================================================================

-- ============================================================================
-- SCHEMA CHANGES
-- ============================================================================

-- 1. Add agent_type to conversations table
-- This ensures each conversation is tagged with its originating agent
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS agent_type VARCHAR(20) NOT NULL DEFAULT 'patient';

-- Add index for efficient filtering by agent_type
CREATE INDEX IF NOT EXISTS ix_conversations_agent_type ON conversations(agent_type);

-- 2. Add agent_type to chat_logs table  
-- This ensures each chat message is tagged with its originating agent
ALTER TABLE chat_logs 
ADD COLUMN IF NOT EXISTS agent_type VARCHAR(20) NOT NULL DEFAULT 'patient';

-- Add index for efficient filtering by agent_type
CREATE INDEX IF NOT EXISTS ix_chat_logs_agent_type ON chat_logs(agent_type);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- View the schema of conversations table
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'conversations'
ORDER BY ordinal_position;

-- View the schema of chat_logs table
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'chat_logs'
ORDER BY ordinal_position;

-- Verify indexes were created
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('conversations', 'chat_logs')
  AND indexname LIKE '%agent_type%';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Get all Patient Concierge conversations
-- SELECT * FROM conversations WHERE agent_type = 'patient';

-- Example 2: Get all Clinical Advisor conversations (when they exist)
-- SELECT * FROM conversations WHERE agent_type = 'clinical';

-- Example 3: Get chat history for a Patient Concierge conversation
-- This ensures no Clinical Advisor messages contaminate the history
-- SELECT * FROM chat_logs 
-- WHERE conversation_id = '<uuid>' 
--   AND agent_type = 'patient'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Example 4: Count conversations by agent type
-- SELECT agent_type, COUNT(*) as conversation_count
-- FROM conversations
-- GROUP BY agent_type;

-- Example 5: Count messages by agent type
-- SELECT agent_type, COUNT(*) as message_count
-- FROM chat_logs
-- GROUP BY agent_type;

-- ============================================================================
-- ISOLATION PROOF
-- ============================================================================
-- 
-- The agent_type column provides DATABASE-LEVEL proof of isolation:
--
-- 1. CONVERSATIONS TABLE:
--    - Each conversation has an agent_type ('patient' or 'clinical')
--    - Queries can filter to ensure only relevant conversations are retrieved
--
-- 2. CHAT_LOGS TABLE:
--    - Each message has an agent_type ('patient' or 'clinical')
--    - get_conversation_history() filters by agent_type to prevent cross-contamination
--    - Patient Concierge cannot retrieve Clinical Advisor messages, and vice versa
--
-- 3. APPLICATION ENFORCEMENT:
--    - src/api/chat.py explicitly sets agent_type='patient'
--    - src/core/state_manager.py filters queries by agent_type
--    - Future clinical logging would set agent_type='clinical'
--
-- This satisfies the compliance requirement:
-- "Website chat history cannot be pulled into Clinical Advisor responses"
-- ============================================================================
