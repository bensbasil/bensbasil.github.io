# Static-First Portfolio Architecture

This repo is intended to keep the public portfolio available even if the
dynamic backend is offline.

## Hosting Model

GitHub Pages is the always-on static shell:

- `/` serves `index.html`
- `/contact.html` serves the contact page
- `/resume.html` serves the resume page
- `/quiz/` serves the static quiz app
- `/medical-rag-app/` serves the built Medical RAG frontend
- `/static/` serves shared images, CSS, and JavaScript

AWS/FastAPI is the optional dynamic layer:

- `https://api.bensbasil.in/contact`
- `https://api.bensbasil.in/quiz/submit`
- `https://api.bensbasil.in/predict/stress`
- `https://api.bensbasil.in/auth/...`
- `https://api.bensbasil.in/api/documents`
- `https://api.bensbasil.in/api/query`
- `https://api.bensbasil.in/health`

If AWS or the API is unavailable, the portfolio should still load. Interactive
features should show a friendly demo/offline message instead of breaking the
page.

## Repository Roles

Static GitHub Pages files:

```text
index.html
contact.html
resume.html
CNAME
projects.json
quiz/
medical-rag-app/
static/
architecture/
```

Backend/API files:

```text
backend/
docker-compose.yml
deployment/
prometheus.yml
```

Local-only/generated files should not be committed:

```text
venv/
.venv/
backend/venv/
node_modules/
__pycache__/
*.log
*.db
backend/chroma_db/
backend/.env
```

## Medical RAG Frontend

For GitHub Pages, `medical-rag-app/` should contain the built static output:

```text
medical-rag-app/
  index.html
  favicon.svg
  icons.svg
  assets/
```

The React/Vite source can live elsewhere, for example:

```text
apps-src/medical-rag/
  package.json
  vite.config.js
  src/
```

When the source is healthy, build it and copy the build output into
`medical-rag-app/`.

## Local Commands

Serve the static portfolio only:

```cmd
cd /d "d:\Bens Files\Portfolio_Website"
run-static.cmd
```

Open:

```text
http://127.0.0.1:5500/
```

Run the optional FastAPI backend:

```cmd
cd /d "d:\Bens Files\Portfolio_Website"
run-api.cmd
```

Open:

```text
http://127.0.0.1:8000/docs
```

Run all local pieces:

```cmd
cd /d "d:\Bens Files\Portfolio_Website"
run-all-local.cmd
```

## Design Rule

Static pages may call the API, but they must not require the API to render.
Treat FastAPI as enhancement, not as the host for the public portfolio.
