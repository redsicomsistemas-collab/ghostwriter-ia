# Ghostwriter con IA

MVP para generar posts de redes sociales con RAG de estilo: guarda publicaciones antiguas, crea embeddings, recupera ejemplos similares al tema nuevo y redacta versiones adaptadas para LinkedIn, X e Instagram.

## Stack

- Backend: FastAPI
- IA: OpenAI API
- Base local: SQLite
- Automatizacion: script CLI, cron/n8n compatible
- Publicacion opcional: Buffer API

## Puesta en marcha

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y agrega `OPENAI_API_KEY`. El modelo queda configurable con `OPENAI_MODEL`; el default actual del proyecto es `gpt-5.2`.

```powershell
.\.venv\Scripts\python -m app.cli init-db
.\.venv\Scripts\python -m app.cli ingest-csv data\sample_posts.csv
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

## Endpoints principales

- `GET /` interfaz web sencilla
- `GET /health`
- `POST /posts/ingest`
- `POST /ideas`
- `POST /generate`
- `GET /drafts`
- `POST /drafts/{draft_id}/approve`
- `POST /drafts/{draft_id}/publish/buffer`

## Flujo recomendado

1. Exporta 50-100 posts tuyos a CSV.
2. Ingiere el CSV para crear embeddings de estilo.
3. Llama `/generate` con un tema o noticia.
4. Revisa los borradores.
5. Publica manualmente o usa Buffer/n8n para aprobar y programar. Para Buffer, reemplaza los valores de `BUFFER_PROFILE_IDS` por los IDs reales de tus perfiles.

## CSV esperado

```csv
platform,text,published_at,url
linkedin,"Texto del post...",2026-04-01,https://...
x,"Texto del tweet...",2026-04-02,https://...
```

## n8n

El archivo `n8n/ghostwriter-flow.json` incluye un flujo base: RSS diario, llamada al backend, y revision humana antes de publicar.

## Deploy en Render

Este repo incluye `render.yaml`. En Render crea un Blueprint o Web Service desde tu repo y usa:

- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Variables necesarias:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `DATABASE_URL`
- `BUFFER_ACCESS_TOKEN` solo si vas a publicar con Buffer
- `BUFFER_PROFILE_IDS` solo si vas a publicar con Buffer

El `render.yaml` usa un disco persistente en `/var/data` y guarda SQLite en `sqlite:////var/data/ghostwriter.db`.
