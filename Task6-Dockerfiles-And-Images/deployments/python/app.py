"""A small Flask application served by Gunicorn in production."""
import os
import platform
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

_notes = [
    {"id": 1, "text": "Multi-stage builds keep the compiler out of production"},
    {"id": 2, "text": "Bind to 0.0.0.0 inside a container, never 127.0.0.1"},
]
_next_id = 3


@app.get("/")
def index():
    return f"""<!doctype html>
<html><head><title>Python Notes API</title></head>
<body style="font-family: system-ui, sans-serif; padding: 40px; max-width: 640px; margin: auto;">
  <h1>Python Notes API</h1>
  <p>Deployed with Docker, served by Gunicorn. Python {platform.python_version()}</p>
  <ul>
    <li><code>GET  /notes</code> — list notes</li>
    <li><code>POST /notes</code> — create <code>{{"text": "..."}}</code></li>
    <li><code>GET  /health</code> — health check</li>
  </ul>
</body></html>"""


@app.get("/notes")
def list_notes():
    return jsonify(_notes)


@app.post("/notes")
def create_note():
    global _next_id
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": "text is required"}), 400
    note = {"id": _next_id, "text": text}
    _next_id += 1
    _notes.append(note)
    return jsonify(note), 201


@app.get("/health")
def health():
    return jsonify(status="ok", time=datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    # Only used for local development; production runs under Gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
