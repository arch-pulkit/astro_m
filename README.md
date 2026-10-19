# ASTR-O

A lightweight recorder for LLM calls. Your application sends each prompt, response and model name to ASTR-O through a small Python SDK. ASTR-O timestamps the record, validates it, and stores it in SQLite, so you can review every call your app made later.

**Live:** https://astrom-production-ad8b.up.railway.app ([interactive API docs](https://astrom-production-ad8b.up.railway.app/docs))

## How it works

```
your app ──► AstroClient (client.py) ──HTTP/JSON──► FastAPI server (app.py) ──► SQLite
```

- **Server (`app.py`):** a FastAPI service. It validates incoming records with Pydantic, so malformed requests are rejected with `422`. It writes rows with parameterized SQL (`?` placeholders), so there's no SQL injection, and returns `500` with a short message if the database fails.
- **SDK (`client.py`):** `AstroClient` wraps the HTTP calls. It generates a UTC ISO-8601 timestamp, validates the record before sending, applies a request timeout, and **never raises or prints**. Every method returns a dict with a `success` key, so a recorder outage can't crash the application that's using it.

## API

| Method | Path | Description | Response |
|---|---|---|---|
| `GET` | `/` | Health check | `{"Status": "OK"}` |
| `POST` | `/records` | Save one record | `{"id": 1, "data": {...}}` |
| `GET` | `/records` | List all records | `[{"id": 1, "prompt": ..., ...}]` |
| `DELETE` | `/records/clear` | Delete all records and reset ids | `{"message": "data cleared"}` |

Record body for `POST /records`:

```json
{
  "prompt": "why do we work?",
  "response": "Fake answer to: why do we work?",
  "timestamp": "2026-10-12T16:41:28.830565+00:00",
  "model_name": "bolty 2.3"
}
```

## Using the SDK

```python
from client import AstroClient

astro = AstroClient()  # base_url argument → ASTRO_BASE_URL env var → http://127.0.0.1:8000

result = astro.save_record(
    prompt="why do we work?",
    response="Fake answer to: why do we work?",
    model_name="bolty 2.3",
)

if result["success"]:
    print("saved with id", result["data"]["id"])
else:
    print("not saved:", result.get("status"), result["error"])

print(astro.get_records())
```

| Method | Returns on success | Returns on failure |
|---|---|---|
| `save_record(prompt, response, model_name)` | `{"success": True, "data": ...}` | `{"success": False, "error": ...}`, plus `"status"` if the server replied |
| `get_records()` | `{"success": True, "data": [...]}` | same shape |
| `clear_database()` | `{"success": True, "message": ...}` | same shape |

## Running locally

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app:app --reload
```

Then open http://127.0.0.1:8000/docs.

To send sample records through the SDK, run this with the server running:

```bash
python sdktest.py
```

> ⚠️ `sdktest.py` **clears the database first**. Don't point it at a database whose records you want to keep.

## Configuration

Both variables are optional, and a `.env` file is loaded automatically.

| Variable | Used by | Default | Example |
|---|---|---|---|
| `ASTRO_DB_PATH` | server | `database.db` next to `app.py` | `sqlite:////data/astro.db` |
| `ASTRO_BASE_URL` | SDK | `http://127.0.0.1:8000` | `https://astrom-production-ad8b.up.railway.app` |

## Tests

```bash
python -m pytest
```

The tests use FastAPI's `TestClient`, so no server needs to be running. A pytest fixture points the app at a temporary SQLite file for each test, so the suite never touches your real database.

## Deployment

Deployed on [Railway](https://railway.com) from this repo. The start command lives in `railway.toml`:

```toml
[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
```

SQLite lives on a Railway **volume**, and `ASTRO_DB_PATH` points to a file inside the volume's mount path. This keeps records across redeploys; without the volume, the container filesystem is wiped on every deploy.

## Known limitations

- **No authentication yet.** Every endpoint is public, including `DELETE /records/clear`. An API key is next on the roadmap.
- SQLite on a single instance, which is fine for a personal recorder but not for many concurrent writers.
- `POST /records` returns the record nested under `data`, while `GET /records` returns flat rows.

## Roadmap

- [ ] API-key authentication for write and delete endpoints
- [ ] Richer records for observability: latency, token counts, cost, errors
- [ ] Separate the SDK's timeout and connection errors, and flag which failures are retryable