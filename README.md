# ASTR-O

A lightweight recorder for LLM calls. Your application sends each prompt, response and model name to ASTR-O through a small Python SDK. ASTR-O timestamps the record, validates it, and stores it in SQLite, so you can review every call your app made later.

The server was originally written in Python with FastAPI and has been rewritten in Go as a learning project. The API is unchanged, so the Python SDK works with it as-is.

**Live:** [https://astrom-production-ad8b.up.railway.app](https://astrom-production-ad8b.up.railway.app)

## How it works

```
your app ──► AstroClient (client.py) ──HTTP/JSON──► Go server (app.go) ──► SQLite
```

- **Server (`app.go`):** a Go service built on the standard library's `net/http` and `database/sql`, with the pure-Go [`modernc.org/sqlite`](https://pkg.go.dev/modernc.org/sqlite) driver (no C compiler needed). It validates incoming JSON itself: missing fields, `null` values or wrong types are rejected with `422`. It writes rows with parameterized SQL (`?` placeholders), so there's no SQL injection. Database failures are logged on the server and return `500` with a short `{"detail": "..."}` message.
- **SDK (`client.py`):** `AstroClient` wraps the HTTP calls. It generates a UTC ISO-8601 timestamp, validates the record before sending, applies a request timeout, and **never raises or prints**. Every method returns a dict with a `success` key, so a recorder outage can't crash the application that's using it.

## API

| Method   | Path             | Description                      | Response                          |
|----------|------------------|----------------------------------|-----------------------------------|
| `GET`    | `/`              | Health check                     | `{"Status": "OK"}`                |
| `POST`   | `/records`       | Save one record                  | `{"id": 1, "data": {...}}`        |
| `GET`    | `/records`       | List all records                 | `[{"id": 1, "prompt": ..., ...}]` |
| `DELETE` | `/records/clear` | Delete all records and reset ids | `{"message": "data cleared"}`     |

Record body for `POST /records`:

```json
{
  "prompt": "why do we work?",
  "response": "Fake answer to: why do we work?",
  "timestamp": "2026-10-12T16:41:28.830565+00:00",
  "model_name": "bolty 2.3"
}
```

All four fields are required. Empty strings are allowed.

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

| Method                                      | Returns on success                  | Returns on failure                                                        |
|---------------------------------------------|-------------------------------------|---------------------------------------------------------------------------|
| `save_record(prompt, response, model_name)` | `{"success": True, "data": ...}`    | `{"success": False, "error": ...}`, plus `"status"` if the server replied |
| `get_records()`                             | `{"success": True, "data": [...]}`  | same shape                                                                |
| `clear_database()`                          | `{"success": True, "message": ...}` | same shape                                                                |

## Running locally

### Server

Requires Go 1.22+.

```bash
go mod tidy   # download dependencies
go run .      # start the server on http://127.0.0.1:8000
```

Or build a standalone binary:

```bash
go build -o astro .
./astro
```

### SDK

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To send sample records through the SDK, run this with the server running:

```bash
python sdktest.py
```

> ⚠️ `sdktest.py` **clears the database first**. Don't point it at a database whose records you want to keep.

## Configuration

All variables are optional, and a `.env` file is loaded automatically.

| Variable         | Used by | Default                                 | Example                                         |
|------------------|---------|-----------------------------------------|-------------------------------------------------|
| `ASTRO_DB_PATH`  | server  | `database.db` in the working directory  | `sqlite:////data/astro.db`                      |
| `PORT`           | server  | `8000`                                  | `8080`                                          |
| `ASTRO_BASE_URL` | SDK     | `http://127.0.0.1:8000`                 | `https://astrom-production-ad8b.up.railway.app` |

The database schema is the same as the original Python version, so existing `database.db` files work with the Go server.

## Testing

Go unit tests are not written yet (see roadmap). For now, `sdktest.py` works as an end-to-end check: start the server, run the script, and confirm that records are saved, listed and cleared.

## Deployment

Deployed on [Railway](https://railway.com) from this repo. Build and start commands live in `railway.toml`:

```toml
[build]
buildCommand = "go build -o astro ."

[deploy]
startCommand = "./astro"
```

Railway provides `PORT` automatically. SQLite lives on a Railway **volume**, and `ASTRO_DB_PATH` points to a file inside the volume's mount path. This keeps records across redeploys; without the volume, the container filesystem is wiped on every deploy.

## Known limitations

- **No authentication yet.** Every endpoint is public, including `DELETE /records/clear`.
- SQLite on a single instance, with the connection pool limited to one connection so writes never collide. Fine for a personal recorder, not for heavy concurrent traffic.
- `POST /records` returns the record nested under `data`, while `GET /records` returns flat rows.
- No auto-generated API docs page (the FastAPI version had `/docs`).
- Validation errors return a single message rather than FastAPI's detailed per-field list.

## Roadmap

- Port the server tests to Go using `net/http/httptest`
- Graceful shutdown on Ctrl+C / redeploy
- API-key authentication for write and delete endpoints
- Richer records for observability: latency, token counts, cost, errors
- Separate the SDK's timeout and connection errors, and flag which failures are retryable