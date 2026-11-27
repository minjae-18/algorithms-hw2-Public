"""HTTP API for the in-memory URL shortener."""

import argparse
import html
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

# Allow this module to be launched as `python3 src/server.py`.
if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hash_table import HashTable
import src.shortener as shortener_module
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

    def _send_html(self, status: int, body: str) -> None:
        encoded_body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_body)))
        self.end_headers()
        self.wfile.write(encoded_body)

    def _page(self, title: str, content: str) -> str:
        return (
            "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<title>{html.escape(title)}</title>"
            "<style>body{font:16px system-ui,sans-serif;max-width:900px;margin:2rem auto;"
            "padding:0 1rem;color:#222}input{box-sizing:border-box;width:100%;padding:.7rem}"
            "button{margin-top:.7rem;padding:.7rem 1rem}table{border-collapse:collapse;"
            "width:100%;margin:1rem 0}th,td{border:1px solid #bbb;padding:.5rem;"
            "text-align:left;vertical-align:top;overflow-wrap:anywhere}code{white-space:pre-wrap}"
            ".bucket{width:5rem}</style></head>"
            f"<body><h1>{html.escape(title)}</h1>{content}</body></html>"
        )

    def _render_hash_table(self, table: HashTable) -> str:
        rows = []
        for bucket_index, head in enumerate(table._buckets):
            entries = []
            node = head
            while node is not None:
                steps = ["h = 0"]
                value = 0
                for character in node.key:
                    code_point = ord(character)
                    previous_value = value
                    value = (previous_value * 31 + code_point) % table.capacity
                    steps.append(
                        f"h = ({previous_value} * 31 + U+{code_point:04X} "
                        f"[{code_point}]) mod {table.capacity} = {value}"
                    )
                calculation = "<br>".join(html.escape(step) for step in steps)
                entries.append(
                    "<li><strong>"
                    f"{html.escape(node.key)}</strong> &rarr; "
                    f"{html.escape(str(node.value))}<br><code>{calculation}</code></li>"
                )
                node = node.next
            chain = "<ol>" + "".join(entries) + "</ol>" if entries else "<em>empty</em>"
            rows.append(f"<tr><th>{bucket_index}</th><td>{chain}</td></tr>")
        return (
            f"<p>capacity = {table.capacity}, entries = {table.size}; "
            "Horner hash: h = (h * 31 + character code point) mod capacity.</p>"
            "<table><thead><tr><th class=\"bucket\">Bucket</th>"
            "<th>Linked-list chain and Horner steps</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )

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
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0]
            is_form = content_type.strip().lower() == "application/x-www-form-urlencoded"
            if is_form:
                fields = parse_qs(body, keep_blank_values=True)
                if len(fields.get("url", [])) != 1:
                    raise ValueError("form must contain one url field")
                url = fields["url"][0]
            else:
                payload = json.loads(body, parse_constant=_reject_json_constant)
                if not isinstance(payload, dict) or "url" not in payload:
                    raise ValueError("request body must be an object with a url field")
                url = payload["url"]
            code = shorten(url)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            self._send_error_json(400, "Invalid request")
            return

        if is_form:
            host = html.escape(self.headers.get("Host", "localhost"), quote=True)
            forwarded_protocol = self.headers.get("X-Forwarded-Proto", "").lower()
            scheme = "https" if forwarded_protocol == "https" else "http"
            short_url = f"{scheme}://{host}/{code}"
            content = (
                "<p>Short link:</p><p><a href=\""
                f"{html.escape(short_url, quote=True)}\">{html.escape(short_url)}</a></p>"
                "<p><a href=\"/\">Make another</a> · <a href=\"/table\">View hash table</a></p>"
            )
            self._send_html(201, self._page("Short URL created", content))
            return

        self._send_json(
            201,
            {"code": code, "short_url": f"/{code}"},
        )

    def do_GET(self) -> None:
        path = self._request_path()
        if path == "/":
            content = (
                "<p>긴 URL을 입력하면 짧은 링크를 만듭니다.</p>"
                "<form action=\"/shorten\" method=\"post\">"
                "<label for=\"url\">URL (http:// 또는 https://)</label>"
                "<input id=\"url\" name=\"url\" type=\"url\" required "
                "placeholder=\"https://example.com\">"
                "<button type=\"submit\">Shorten URL</button></form>"
                "<p><a href=\"/table\">View hash table</a></p>"
            )
            self._send_html(200, self._page("URL Shortener", content))
            return
        if path == "/table":
            content = self._render_hash_table(shortener_module._url_to_id)
            content += "<p><a href=\"/\">Back to URL shortener</a></p>"
            self._send_html(200, self._page("Hash table buckets", content))
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
