# ResearchGPT

ResearchGPT is an academic research paper intelligence workspace. This repository is being built in phases; the current foundation contains an initial dashboard, API health endpoints, and PostgreSQL development configuration.

## Current status

Phases 1–3 are implemented: the dashboard, account flows, protected paper/collection APIs, PDF processing, semantic search, and structured summaries are in place. Authentication requires a configured JWT secret and migrated database. OCR for scanned PDFs and additional authentication hardening remain future work.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer
- Docker Desktop with Docker Compose (or a local PostgreSQL 16 instance)

## Local setup

1. Copy `.env.example` to `.env` in the repository root.
2. Replace `JWT_SECRET_KEY` in `.env` with at least 32 random characters. For example, run `python -c "import secrets; print(secrets.token_urlsafe(48))"` and copy the output.
3. Start PostgreSQL with `docker compose up -d db`.
4. In a terminal, install backend dependencies and run the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

5. In another terminal, install frontend dependencies and run Vite:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. Register an account, then upload and organize PDFs from **My papers** and **Collections**. The API documentation is at `http://localhost:8000/docs`; `/api/v1/health` checks the API, `/api/v1/health/ready` checks the database connection, and protected `/api/v1/dashboard/summary` returns per-user dashboard counts.

The migrations create the account, paper, page, chunk, collection, conversation, report, agent workflow, and revoked-token tables. Apply future schema changes with Alembic migrations rather than creating tables manually. Uploaded PDFs are stored beneath `data/uploads/<user-id>/` using generated storage names; original filenames are metadata only. Uploads accept PDF files up to 25 MB each and 20 files per batch.

PDFs are processed in the background. PyMuPDF extracts selectable page text and available metadata; chunk size and overlap are configurable. Sentence Transformers creates embeddings using `EMBEDDING_MODEL_NAME`. On Windows, persistent normalized vectors use the NumPy exact-search fallback because FAISS pip wheels are not officially supported there; on supported non-Windows pip platforms, FAISS is installed and used. The stored vectors are durable and the FAISS index can be rebuilt from database chunk embeddings.

Short or detailed structured summaries can be requested from the paper detail page. The overview uses the configured pretrained Transformers model (`SUMMARY_MODEL_NAME`) with hierarchical map-reduce summarization for long papers. The model weights download from Hugging Face on first use and may require significant disk space and memory. No summary is fabricated if the model cannot load; the job records a visible failure. Structured fields are extracted from the paper text and say when a field is not stated. Scanned PDFs currently report that OCR is needed rather than being treated as successfully extracted.

## Configuration

Settings are read from environment variables or a root `.env` file. See `.env.example`. Database credentials are local development defaults and should be changed for any shared or deployed environment.

