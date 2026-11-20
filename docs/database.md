# Database foundation

PostgreSQL is the source of truth for application records. SQLAlchemy models live in `backend/app/models/entities.py`; Alembic manages schema versions under `backend/alembic/`.

## Relationships

- A user owns papers, collections, conversations, reports, and agent runs.
- Collections and papers have a many-to-many relationship through `collection_papers`.
- Each paper has page text and retrieval chunks. Chunks keep their source page range and a vector index key; vector data itself belongs in the persistent FAISS index.
- Conversations contain ordered messages. Message citations are stored as structured JSON linking to paper and page references.
- Agent runs contain task results with individual statuses and structured output.

## Apply migrations

From the `backend` directory, with the virtual environment active and PostgreSQL running:

```powershell
alembic upgrade head
```

The initial migration is `0001_initial_schema`. Generate later revisions with `alembic revision --autogenerate -m "describe change"`, inspect the generated operations, then apply with `alembic upgrade head`.

