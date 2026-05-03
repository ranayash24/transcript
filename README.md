# Video Scene Intelligence

A full-stack AI-powered web app that lets you upload any video and ask natural language questions about its content. It automatically transcribes speech, captions keyframes, and uses semantic search to find relevant moments — returning answers with precise timestamps.

---

## What It Does

- **Upload a video** (MP4, up to 500MB)
- **AI pipeline runs automatically:**
  - Extracts keyframes every 5 seconds using FFmpeg
  - Transcribes speech using Whisper (runs locally, no API cost)
  - Captions keyframes using Google Gemini Vision
  - Fuses transcript + captions into segments
  - Embeds and indexes everything into a vector database
- **Ask questions in natural language** — e.g. *"When does the speaker talk about revenue?"*
- **Get streaming answers with timestamps** like `[02:34]` so you can jump directly to the moment

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, SQLAlchemy (async) |
| Task Queue | Celery + Redis |
| Speech-to-Text | faster-whisper (local) |
| Vision + Q&A | Google Gemini API (free tier) |
| Embeddings | Gemini `gemini-embedding-001` (3072-dim) |
| Vector DB | Qdrant |
| Object Storage | MinIO (self-hosted S3-compatible) |
| Database | PostgreSQL |
| Infrastructure | Docker Compose |

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- FFmpeg (`brew install ffmpeg` on Mac)
- A free [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

### 1. Clone the repo

```bash
git clone https://github.com/ranayash24/transcript.git
cd transcript
```

---

### 2. Start infrastructure (PostgreSQL, Redis, MinIO, Qdrant)

```bash
docker compose -f docker-compose.infra.yml up -d
```

---

### 3. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example env file and fill in your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/vsi
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
MINIO_ENDPOINT_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=video-scene-intelligence
QDRANT_URL=http://localhost:6333
GEMINI_API_KEY=your_gemini_api_key_here
WHISPER_MODEL=base
```

Run database migrations:

```bash
alembic upgrade head
```

---

### 4. Run the backend (Terminal 1)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

### 5. Run the Celery worker (Terminal 2)

```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

> `--pool=solo` is required on macOS to prevent crashes. On Linux you can omit it.

---

### 6. Set up and run the frontend (Terminal 3)

```bash
cd frontend
npm install
npm run dev
```

---

### 7. Open the app

Visit **http://localhost:3000**

---

## How to Deploy

### Recommended Stack (free / low-cost)

| Service | Used For | Cost |
|---|---|---|
| [Vercel](https://vercel.com) | Frontend hosting | Free |
| [Railway](https://railway.app) | Backend + Celery worker | ~$5/mo |
| [Upstash Redis](https://upstash.com) | Celery broker | Free tier |
| [Qdrant Cloud](https://cloud.qdrant.io) | Vector database | Free tier |
| [Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/) | Object storage | Free tier |
| [Supabase](https://supabase.com) | PostgreSQL | Free tier |

---

### Deploy Frontend to Vercel

```bash
cd frontend
npx vercel --prod
```

Set environment variable in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

---

### Deploy Backend to Railway

1. Create a new project on [railway.app](https://railway.app)
2. Connect your GitHub repo
3. Set the root directory to `backend`
4. Add all environment variables from `.env` (update URLs to point to cloud services)
5. Railway will auto-detect the `Dockerfile` and deploy

---

### Deploy Celery Worker to Railway

1. Add a second service in the same Railway project
2. Set root directory to `backend`
3. Override the start command:
   ```
   celery -A app.workers.celery_app worker --loglevel=info
   ```

---

## Project Structure

```
transcript/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── models/       # SQLAlchemy DB models
│   │   ├── services/     # LLM, storage, vector DB
│   │   └── workers/      # Celery pipeline tasks
│   ├── alembic/          # DB migrations
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React UI components
│   └── lib/              # API client, SSE helpers
└── docker-compose.infra.yml
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/videos/upload` | Upload a video file |
| `GET` | `/api/videos/{id}` | Get video status and metadata |
| `GET` | `/api/jobs/{id}` | Get pipeline job progress |
| `POST` | `/api/query/{video_id}` | Ask a question (streaming SSE) |

---

## Notes

- Whisper runs **locally** — no API key needed for transcription
- Gemini free tier allows **1,500 requests/day** for text and **50 requests/day** for vision
- The pipeline caps Gemini vision calls at **3 per video** to stay within free tier limits
- Videos are stored in MinIO locally (or swap for Cloudflare R2 / AWS S3 in production)
