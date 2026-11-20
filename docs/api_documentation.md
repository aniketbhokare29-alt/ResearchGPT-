# API reference

Base URL during local development: `http://localhost:8000/api/v1`

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

`analyzed_papers` counts papers whose processing status is `completed`. Authentication and per-user scoping are scheduled for Phase 2; this interim endpoint returns counts only.
