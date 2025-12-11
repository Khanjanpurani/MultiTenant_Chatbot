# Project Flow Overview for MultiTenant_Chatbot

This file summarizes the main flow and architecture of the MultiTenant_Chatbot project for quick understanding.

## Main Components

- **FastAPI Application** (`src/main.py`):
  - Entry point for the API server.
  - Registers routers for chat, admin, and clinical endpoints.
  - Handles CORS, logging, and root endpoints.

- **Routers**:
  - `src/api/chat.py`: Patient-facing chatbot (stateful, appointment booking, uses Pinecone RAG, persists conversation, triggers webhooks).
  - `src/api/clinical.py`: Doctor-facing clinical advisor (stateless, uses practice profile, supports text/image, protected by token).
  - `src/api/admin.py`: Admin endpoints for retrieving finalized leads.

- **Database Models** (`src/models/models.py`):
  - `Client`: Represents a clinic/client.
  - `Conversation`: Tracks chat sessions and their state.
  - `ChatLog`: Stores individual chat messages.

- **Core Utilities**:
  - `src/core/db.py`: Database connection and session management.
  - `src/core/config.py`: Loads environment variables and configures database/API keys.

## Typical Flow

1. **Patient Chat (Door 1)**
   - User interacts via `/api/chat` endpoint.
   - State machine manages conversation stages (greeting, booking, answering, closing).
   - Data is stored in the database, and webhooks are triggered on appointment finalization.

2. **Clinical Advisor (Door 2)**
   - Doctor interacts via `/api/clinical` endpoint.
   - Stateless conversation, uses practice profile and supports image input.
   - Protected by client token.

3. **Admin**
   - Admin retrieves leads via `/api/admin/leads/{client_id}`.
   - Shows finalized conversations for follow-up.

## Configuration
- Environment variables are loaded from `.env` (see `src/core/config.py`).
- Database is PostgreSQL, configured via `DATABASE_URL`.
- External APIs: OpenAI, Pinecone.

## How to Run
1. Create and activate a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Set up environment variables in `.env`.
4. Run the FastAPI server (e.g., `uvicorn src.main:app --reload`).

---
This file is auto-generated for onboarding and quick reference. For details, see the respective source files.
