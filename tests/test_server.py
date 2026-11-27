import http.client
import json
import signal
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import src.shortener as shortener_module
from src.hash_table import HashTable
from src.server import ShortenerRequestHandler


class ShortenerServerTests(unittest.TestCase):
    def setUp(self):
        shortener_module._url_to_id = HashTable()
        shortener_module._id_to_url = HashTable()
        shortener_module._next_id = 0

        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), ShortenerRequestHandler
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port)
        connection.request(method, path, body=body)
        response = connection.getresponse()
        result = response.status, response.getheaders(), response.read()
        connection.close()
        return result

    def test_custom_port_and_restart_clears_memory(self):
        project_root = Path(__file__).resolve().parents[1]
        with socket.socket() as port_socket:
            port_socket.bind(("127.0.0.1", 0))
            port = port_socket.getsockname()[1]

        def start_server():
            return subprocess.Popen(
                [
                    sys.executable,
                    str(project_root / "src" / "server.py"),
                    "--port",
                    str(port),
                ],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        def stop_server(process):
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                process.wait(timeout=5)

        def wait_until_ready():
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", port, timeout=1
                    )
                    connection.request("GET", "/")
                    response = connection.getresponse()
                    status = response.status
                    response.read()
                    connection.close()
                    return status
                except OSError:
                    time.sleep(0.02)
            self.fail("server did not start on the requested port")

        process = start_server()
        try:
            self.assertEqual(wait_until_ready(), 400)
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            connection.request(
                "POST",
                "/shorten",
                body=json.dumps({"url": "https://example.com"}),
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 201)
            self.assertEqual(json.loads(response.read())["code"], "0")
            connection.close()
        finally:
            stop_server(process)

        process = start_server()
        try:
            self.assertEqual(wait_until_ready(), 400)
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            connection.request("GET", "/0")
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            connection.close()
        finally:
            stop_server(process)

    def test_post_shorten_returns_json_and_existing_code(self):
        body = json.dumps({"url": "https://example.com/path"})

        status, headers, response_body = self.request("POST", "/shorten", body)

        self.assertEqual(status, 201)
        self.assertIn(("Content-Type", "application/json"), headers)
        self.assertEqual(
            json.loads(response_body),
            {"code": "0", "short_url": "/0"},
        )

        status, _, response_body = self.request("POST", "/shorten", body)
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(response_body)["code"], "0")

    def test_post_shorten_rejects_empty_malformed_and_invalid_payloads(self):
        invalid_bodies = [
            b"",
            b"\xff",
            b'{"url":',
            b'{"url": "https://example.com", "extra": NaN}',
            b"[]",
            b"{}",
            b'{"url": 3}',
            b'{"url": "relative"}',
        ]

        for body in invalid_bodies:
            with self.subTest(body=body):
                status, headers, response_body = self.request(
                    "POST", "/shorten", body
                )
                self.assertEqual(status, 400)
                self.assertIn(("Content-Type", "application/json"), headers)
                self.assertIsInstance(json.loads(response_body), dict)

    def test_get_short_code_redirects_to_original_url(self):
        original_url = "https://example.com/path?q=1"
        self.request("POST", "/shorten", json.dumps({"url": original_url}))

        status, headers, body = self.request("GET", "/0")

        self.assertEqual(status, 302)
        self.assertIn(("Location", original_url), headers)
        self.assertEqual(body, b"")

    def test_get_rejects_root_and_invalid_or_unknown_codes(self):
        for path, expected_status in [
            ("/", 400),
            ("///0", 400),
            ("/bad!", 400),
            ("/unknown", 404),
        ]:
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, expected_status)

    def test_unsupported_path_and_method_return_errors(self):
        status, _, _ = self.request("POST", "/unknown", "{}")
        self.assertEqual(status, 404)

        status, _, _ = self.request("POST", "///shorten", "{}")
        self.assertEqual(status, 404)

        for method in ("PUT", "BREW"):
            with self.subTest(method=method):
                status, headers, response_body = self.request(method, "/shorten")
                self.assertEqual(status, 405)
                self.assertIn(("Content-Type", "application/json"), headers)
                self.assertIsInstance(json.loads(response_body), dict)


if __name__ == "__main__":
    unittest.main()
