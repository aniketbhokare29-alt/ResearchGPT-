# ResearchGPT

ResearchGPT is an academic research paper intelligence workspace. This repository is being built in phases; the current foundation contains an initial dashboard, API health endpoints, and PostgreSQL development configuration.

## Current status

Phase 1 implementation is complete: the dashboard reads aggregate counts from the API, and the backend, database schema, initial migration, and responsive navigation are in place. Runtime startup still requires installing dependencies and running PostgreSQL. Paper processing, authentication, AI analysis, and reports are later milestones.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- Docker Desktop with Docker Compose (or a local PostgreSQL 16 instance)

## Local setup

1. Copy `.env.example` to `.env` in the repository root.
2. Start PostgreSQL with `docker compose up -d db`.
3. In a terminal, install backend dependencies and run the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

4. In another terminal, install frontend dependencies and run Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. The API documentation is at `http://localhost:8000/docs`; `/api/v1/health` checks the API, `/api/v1/health/ready` checks the database connection, and `/api/v1/dashboard/summary` returns aggregate dashboard counts. Until Phase 2 adds authentication, that summary is workspace-wide and contains counts only.

The initial migration creates the account, paper, page, chunk, collection, conversation, report, and agent workflow tables. Apply future schema changes with Alembic migrations rather than creating tables manually.

## Configuration

Settings are read from environment variables or a root `.env` file. See `.env.example`. Database credentials are local development defaults and should be changed for any shared or deployed environment.

