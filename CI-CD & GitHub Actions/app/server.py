"""Tiny HTTP front-end for the calculator so the image can run as a service.

The instructor's calculator.py is an interactive CLI (it blocks on input()),
which cannot be deployed to Kubernetes or smoke-tested by a pipeline. This
module wraps the same add/subtract/multiply/divide functions in a JSON API
using only the standard library, so the image needs no extra dependencies.

Endpoints:
  GET /                                 -> app info (name, version)
  GET /health                           -> {"status": "ok"}
  GET /calculate?a=10&b=5&op=add        -> {"a": 10.0, "b": 5.0, "op": "add", "result": 15.0}
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.calculator import add, divide, multiply, subtract

OPERATIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}

APP_NAME = "session16-calculator"
APP_VERSION = os.environ.get("APP_VERSION", "dev")


def calculate(a, b, op):
    """Pure function used by the HTTP handler (and unit-tested directly)."""
    if op not in OPERATIONS:
        raise ValueError(f"Unknown operation '{op}'. Valid: {sorted(OPERATIONS)}")
    return OPERATIONS[op](float(a), float(b))


class CalculatorHandler(BaseHTTPRequestHandler):
    server_version = "Session16Calculator/1.0"

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (name required by BaseHTTPRequestHandler)
        url = urlparse(self.path)
        if url.path == "/":
            self._send_json(200, {"app": APP_NAME, "version": APP_VERSION,
                                  "endpoints": ["/health", "/calculate?a=&b=&op="]})
        elif url.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif url.path == "/calculate":
            params = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                a, b, op = params["a"], params["b"], params.get("op", "add")
                result = calculate(a, b, op)
            except KeyError:
                self._send_json(400, {"error": "query parameters 'a' and 'b' are required"})
                return
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"a": float(a), "b": float(b), "op": op, "result": result})
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}", flush=True)


def make_server(host="0.0.0.0", port=8000):  # nosec B104 - must listen on all interfaces inside a container
    return ThreadingHTTPServer((host, port), CalculatorHandler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"{APP_NAME} {APP_VERSION} listening on :{port}", flush=True)
    make_server(port=port).serve_forever()
