# Database Schema - Before and After Migration

## BEFORE Migration (Vulnerable to Cross-Contamination)

### conversations Table
```
┌─────────────────────┬──────────────┬──────────┐
│ Column Name         │ Type         │ Nullable │
├─────────────────────┼──────────────┼──────────┤
│ conversation_id     │ UUID         │ NO       │ (PK)
│ client_id           │ UUID         │ NO       │ (FK)
│ current_stage       │ VARCHAR(50)  │ NO       │
│ conversation_state  │ JSON         │ YES      │
│ last_activity_at    │ TIMESTAMP    │ YES      │
│ is_finalized        │ BOOLEAN      │ NO       │
│ finalized_at        │ TIMESTAMP    │ YES      │
└─────────────────────┴──────────────┴──────────┘
```

### chat_logs Table
```
┌─────────────────────┬──────────────┬──────────┐
│ Column Name         │ Type         │ Nullable │
├─────────────────────┼──────────────┼──────────┤
│ log_id              │ BIGINT       │ NO       │ (PK)
│ conversation_id     │ UUID         │ NO       │ (FK)
│ sender_type         │ VARCHAR(10)  │ NO       │
│ message             │ VARCHAR      │ NO       │
│ created_at          │ TIMESTAMP    │ YES      │
│ response_time_ms    │ INTEGER      │ YES      │
└─────────────────────┴──────────────┴──────────┘
```

**PROBLEM:** No way to distinguish Patient Concierge conversations from 
Clinical Advisor conversations!

---

## AFTER Migration (Fully Isolated)

### conversations Table
```
┌─────────────────────┬──────────────┬──────────┬─────────────┐
│ Column Name         │ Type         │ Nullable │ Default     │
├─────────────────────┼──────────────┼──────────┼─────────────┤
│ conversation_id     │ UUID         │ NO       │             │ (PK)
│ client_id           │ UUID         │ NO       │             │ (FK)
│ current_stage       │ VARCHAR(50)  │ NO       │ 'GREETING'  │
│ conversation_state  │ JSON         │ YES      │ {}          │
│ last_activity_at    │ TIMESTAMP    │ YES      │ now()       │
│ is_finalized        │ BOOLEAN      │ NO       │ false       │
│ finalized_at        │ TIMESTAMP    │ YES      │             │
│ agent_type          │ VARCHAR(20)  │ NO       │ 'patient'   │ ✅ NEW
└─────────────────────┴──────────────┴──────────┴─────────────┘

INDEX: ix_conversations_agent_type ON agent_type ✅ NEW
```

### chat_logs Table
```
┌─────────────────────┬──────────────┬──────────┬─────────────┐
│ Column Name         │ Type         │ Nullable │ Default     │
├─────────────────────┼──────────────┼──────────┼─────────────┤
│ log_id              │ BIGINT       │ NO       │             │ (PK)
│ conversation_id     │ UUID         │ NO       │             │ (FK)
│ sender_type         │ VARCHAR(10)  │ NO       │             │
│ message             │ VARCHAR      │ NO       │             │
│ created_at          │ TIMESTAMP    │ YES      │ now()       │
│ response_time_ms    │ INTEGER      │ YES      │             │
│ agent_type          │ VARCHAR(20)  │ NO       │ 'patient'   │ ✅ NEW
└─────────────────────┴──────────────┴──────────┴─────────────┘

INDEX: ix_chat_logs_agent_type ON agent_type ✅ NEW
```

**SOLUTION:** agent_type column ensures complete isolation!

---

## Isolation Enforcement

### Code Flow for Patient Concierge (Door 1)
```
/api/chat endpoint
    │
    ├─> load_or_create_conversation(agent_type='patient')
    │       └─> Creates conversation with agent_type='patient'
    │
    ├─> get_conversation_history(agent_type='patient')  
    │       └─> Filters: WHERE agent_type='patient'
    │       └─> CANNOT retrieve Clinical Advisor messages
    │
    ├─> log_message(agent_type='patient')
    │       └─> Logs message with agent_type='patient'
    │
    └─> log_message(agent_type='patient')
            └─> Logs response with agent_type='patient'
```

### Code Flow for Clinical Advisor (Door 2)
```
/api/clinical/chat endpoint
    │
    └─> STATELESS - No database logging
        └─> Client maintains conversation history
        └─> No risk of pulling Patient Concierge data
```

---

## Compliance Statement

✅ **Patient Concierge conversations are tagged with agent_type='patient'**

✅ **All Patient Concierge messages are tagged with agent_type='patient'**

✅ **get_conversation_history() filters by agent_type to prevent cross-contamination**

✅ **Database schema provides verifiable proof of isolation**

✅ **Indexes ensure efficient filtering without performance degradation**

---

## Migration Details

**File:** `alembic/versions/0003_add_agent_type_for_subagent_isolation.py`

**Changes:**
1. Add `agent_type VARCHAR(20) NOT NULL DEFAULT 'patient'` to `conversations`
2. Add `agent_type VARCHAR(20) NOT NULL DEFAULT 'patient'` to `chat_logs`
3. Create index `ix_conversations_agent_type` on `conversations(agent_type)`
4. Create index `ix_chat_logs_agent_type` on `chat_logs(agent_type)`

**Backward Compatible:** YES (default value 'patient' applied to existing rows)

**Rollback Available:** YES (downgrade removes columns and indexes)
