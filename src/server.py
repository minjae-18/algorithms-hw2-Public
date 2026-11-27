"""HTTP API for the in-memory URL shortener."""

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Allow this module to be launched as `python3 src/server.py`.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shortener import expand, shorten


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


class ShortenerRequestHandler(BaseHTTPRequestHandler):
    """Handle URL shortening and redirection requests."""

    def _request_path(self) -> str:
        request_parts = self.raw_requestline.split(b" ", 2)
        if len(request_parts) < 2:
            return self.path.split("?", 1)[0]
        return request_parts[1].decode("iso-8859-1").split("?", 1)[0]

    def _send_json(self, status: int, payload: dict[str, str]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message})

    def do_POST(self) -> None:
        if self._request_path() != "/shorten":
            self._send_error_json(404, "Not Found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                raise ValueError("request body is empty")
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body, parse_constant=_reject_json_constant)
            if not isinstance(payload, dict) or "url" not in payload:
                raise ValueError("request body must be an object with a url field")
            code = shorten(payload["url"])
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            self._send_error_json(400, "Invalid request")
            return

        self._send_json(
            201,
            {"code": code, "short_url": f"/{code}"},
        )

    def do_GET(self) -> None:
        path = self._request_path()
        if path == "/":
            self._send_error_json(400, "Short code is required")
            return
        if not path.startswith("/") or "/" in path[1:]:
            self._send_error_json(400, "Invalid short code")
            return

        code = path[1:]
        try:
            url = expand(code)
        except ValueError:
            self._send_error_json(400, "Invalid short code")
            return
        except KeyError:
            self._send_error_json(404, "Short code not found")
            return

        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _method_not_allowed(self) -> None:
        self._send_error_json(405, "Method Not Allowed")

    do_DELETE = _method_not_allowed
    do_HEAD = _method_not_allowed
    do_OPTIONS = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_PUT = _method_not_allowed
    do_TRACE = _method_not_allowed
    do_CONNECT = _method_not_allowed

    def send_error(self, code, message=None, explain=None) -> None:
        if code == 501:
            self._method_not_allowed()
            return
        super().send_error(code, message, explain)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP server.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    server = ThreadingHTTPServer(("", args.port), ShortenerRequestHandler)
    try:
        print(f"Serving on port {args.port}")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
