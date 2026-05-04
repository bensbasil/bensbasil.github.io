# Portfolio Website

Static-first portfolio with optional FastAPI-powered dynamic features.

## Architecture

GitHub Pages is the always-on public site:

- `index.html` - main portfolio
- `contact.html` - contact page
- `resume.html` - resume page
- `quiz/` - static quiz frontend
- `medical-rag-app/` - built static Medical RAG frontend
- `static/` - shared assets

AWS/FastAPI powers optional live features:

- contact form submission
- quiz result submission and analytics
- stress prediction
- auth/profile endpoints
- Medical RAG document/query endpoints

The static pages should still load if the API is offline. Live features should
show a friendly fallback message instead of breaking the page.

## Run Static Site Locally

Fast path:

```cmd
run-static.cmd
```

Manual equivalent:

```cmd
cd /d "d:\Bens Files\Portfolio_Website"
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500/
```

## Run FastAPI Backend Locally

First-time setup:

```cmd
cd /d "d:\Bens Files\Portfolio_Website\backend"
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Fast path:

```cmd
run-api.cmd
```

Manual equivalent:

```cmd
cd /d "d:\Bens Files\Portfolio_Website\backend"
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Run Everything Locally

From the repo root:

```cmd
run-all-local.cmd
```

This opens separate CMD windows for:

- static portfolio frontend: `http://127.0.0.1:5500/`
- portfolio API backend: `http://127.0.0.1:8000/docs`
- Medical RAG API backend: `http://127.0.0.1:8002/api/health`

## Medical RAG Frontend

`medical-rag-app/` is intended to contain the built static files that GitHub
Pages can serve directly.

If you want editable React/Vite source, keep it separately, for example:

```text
apps-src/medical-rag/
```

Then build from the source project and copy the resulting static output into
`medical-rag-app/`.

## More Detail

See `STATIC_FIRST_ARCHITECTURE.md`.
