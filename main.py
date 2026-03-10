from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from routes import router
import models

# Create tables on startup
models.Base.metadata.create_all(bind=models.engine)

app = FastAPI()

# Include all routes (no prefix, works with or without /api)

@app.middleware("http")
async def normalize_api_prefix(request: Request, call_next):
    if request.scope.get("path", "").startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:] or "/"
    return await call_next(request)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def root():
    html = """
    <html>
    <head>
        <title>LinkSage API</title>
        <style>
            body { background-color: #121212; color: #e0e0e0; font-family: Arial, Helvetica, sans-serif; padding: 2rem; }
            h1 { color: #4fd1c5; }
            a { color: #82aaff; }
            .endpoint { margin-bottom: 1rem; }
            .code { background: #1e1e1e; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>LinkSage – Intelligent Bookmark Manager</h1>
        <p>AI‑native backend built with FastAPI, PostgreSQL, and DigitalOcean Serverless Inference.</p>
        <h2>Available Endpoints</h2>
        <div class="endpoint"><span class="code">GET /health</span> – health check</div>
        <div class="endpoint"><span class="code">POST /summarize</span> – generate a summary for a URL</div>
        <div class="endpoint"><span class="code">POST /generate-tags</span> – generate tags for a URL</div>
        <div class="endpoint"><span class="code">POST /bookmarks</span> – save a bookmark (AI summary + tags if omitted)</div>
        <div class="endpoint"><span class="code">GET /bookmarks</span> – list all bookmarks</div>
        <h2>Documentation</h2>
        <p><a href="/docs" target="_blank">Swagger UI</a> | <a href="/redoc" target="_blank">ReDoc</a></p>
        <h2>Tech Stack</h2>
        <ul>
            <li>FastAPI 0.115.0</li>
            <li>PostgreSQL via SQLAlchemy 2.0.35</li>
            <li>DigitalOcean Serverless Inference (model: openai-gpt-oss-120b)</li>
            <li>Python 3.12+</li>
        </ul>
    </body>
    </html>
    """
    return html
