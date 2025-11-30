# KorepetytorAI Backend (MVP)

Minimal FastAPI backend for KorepetytorAI. Provides registration/login with JWT, chat via OpenAI, and a simple leaderboard. Uses SQLite by default.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The backend uses the modern OpenAI Python SDK (>=1.3) required by the
   `openai.OpenAI` client used in the chat endpoint.
2. Set environment variables:
   ```bash
   export SECRET_KEY="your-secret-key"
   export OPENAI_API_KEY="your-openai-key"
   # Optional: override database location (defaults to local SQLite file)
   export DATABASE_URL="sqlite:///./korepetytorai_dev.db"
   ```

## Running locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

To verify the API is reachable locally, call the health endpoint:

```bash
curl http://localhost:8000/health
```

## Deploying to Railway

The repository includes a `Dockerfile` used by Railway. Set the environment variables in
Railway (Project → Variables):

- `SECRET_KEY`
- `OPENAI_API_KEY`
- optionally `DATABASE_URL` if you want something other than the default SQLite file

With those set, Railway will build the container and run:

```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Running via Docker locally

Build and run the image to mirror the Railway setup:

```bash
docker build -t korepetytorai .
docker run -p 8000:8000 --env-file .env korepetytorai
```

## Key endpoints
- `POST /auth/register` – create a new student account.
- `POST /auth/login` – obtain a JWT access token.
- `POST /chat` – send a message (requires `Authorization: Bearer <token>`).
- `GET /leaderboard` – list top students by XP.
- `GET /health` – health check.

The app auto-creates tables on startup. By default, it uses `korepetytorai_dev.db` in the
project root; set `DATABASE_URL` to point to another database if needed.
