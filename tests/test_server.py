import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from vivint_bridge.server import make_handler


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler("test", "")
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get_json(self, path: str) -> tuple[int, dict]:
        with urlopen(f"{self.base_url}{path}", timeout=2) as response:
            return response.status, json.load(response)

    def test_health_distinguishes_service_from_bridge(self) -> None:
        status, payload = self.get_json("/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(payload["service_health"], "ok")
        self.assertEqual(payload["bridge_state"], "blocked")

    def test_status_disables_commands_and_panel_writes(self) -> None:
        status, payload = self.get_json("/status")
        self.assertEqual(status, 200)
        self.assertFalse(payload["commands_enabled"])
        self.assertFalse(payload["safety"]["panel_writes"])
        self.assertFalse(payload["panel_host_configured"])

    def test_unknown_route_returns_404(self) -> None:
        with self.assertRaises(HTTPError) as raised:
            urlopen(f"{self.base_url}/missing", timeout=2)
        try:
            self.assertEqual(raised.exception.code, 404)
        finally:
            raised.exception.close()


if __name__ == "__main__":
    unittest.main()

