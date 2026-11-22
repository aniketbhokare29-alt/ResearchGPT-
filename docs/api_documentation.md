# API reference

Base URL during local development: `http://localhost:8000/api/v1`

Protected endpoints use `Authorization: Bearer <access_token>`. Access tokens expire after the configured `ACCESS_TOKEN_MINUTES`. Logout revokes the current token in the database.

## Health

### `GET /health`

Checks that the API process responds.

Example response:

```json
{"status":"ok","service":"api"}
```

### `GET /health/ready`

Checks database connectivity. Returns `200` when connected; database connection errors return `503`.

## Dashboard

### `GET /dashboard/summary`

Returns aggregate counts used by the dashboard cards.

```json
{
  "papers": 0,
  "analyzed_papers": 0,
  "collections": 0,
  "reports": 0
}
```

`analyzed_papers` counts this user's papers whose processing status is `completed`.

## Authentication

- `POST /auth/register` accepts `email`, `password` (10–128 characters), and optional `full_name`; returns a bearer token and profile.
- `POST /auth/login` accepts email and password; invalid credentials return a generic `401` response.
- `POST /auth/logout` revokes the current bearer token.
- `GET /auth/me` returns the signed-in user's profile.
- `PATCH /auth/me` updates `full_name`.

JWT signing requires `JWT_SECRET_KEY` with at least 32 random characters. Passwords are hashed with Argon2 through pwdlib; plain text passwords are never stored.

## Papers

- `GET /papers?offset=0&limit=50` lists the signed-in user's paper records.
- `POST /papers/upload` accepts repeated multipart `files` fields with up to 20 PDFs per request. Each file is limited to 25 MB and checked for a `.pdf` name and PDF header. The response gives each file an `uploaded`, `duplicate`, or `rejected` status.
- `GET /papers/{paper_id}` returns a paper owned by the current user.
- `DELETE /papers/{paper_id}` deletes its record and stored PDF.

- `GET /papers/{paper_id}/pages?offset=0&limit=10` returns extracted text with one-based page numbers.
- `POST /papers/{paper_id}/process` queues extraction and indexing again when processing is pending or failed.
- `GET /papers/search?q=...&top_k=8` performs semantic search across the user's indexed papers. Optional `paper_id` or `collection_id` narrows the search scope.
- `POST /papers/{paper_id}/summary?detail=short|detailed` queues structured summary generation and returns `202`.

Uploaded PDFs use generated storage keys under the configured upload directory. Duplicate hashes are checked per user. New uploads have status `pending` and are queued for processing.

Uploads are queued for page extraction, chunking, embedding, and indexing. Paper records expose `processing_status`, `processing_step`, and `processing_error`; summary state is separate in `summary_status` and `summary_error`. Text extraction and semantic search need the configured embedding model. Summaries additionally need the configured Transformers model weights.

## Collections

- `GET /collections` and `POST /collections` list and create the signed-in user's collections.
- `PATCH /collections/{collection_id}` edits its name or description.
- `DELETE /collections/{collection_id}` removes a collection while preserving its papers in the library.
- `GET /collections/{collection_id}/papers` lists its papers.
- `PUT /collections/{collection_id}/papers/{paper_id}` adds a paper; repeating the request is safe.
- `DELETE /collections/{collection_id}/papers/{paper_id}` removes the paper from that collection.
