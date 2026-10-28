import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from vivint_bridge.panel import PanelProbeResult, normalize_fingerprint
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


class ConfiguredPanelTests(unittest.TestCase):
    def test_normalize_fingerprint(self) -> None:
        self.assertEqual(normalize_fingerprint("AA:bb:01"), "AABB01")

    def test_status_reports_reachable_authentication_boundary(self) -> None:
        probe = PanelProbeResult(
            host="192.0.2.10",
            port=8443,
            reachable=True,
            tls=True,
            http_status=401,
            server="Python/aiohttp",
            certificate_sha256="ABC123",
            certificate_matches_pin=True,
        )

        with patch("vivint_bridge.server.probe_panel", return_value=probe):
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                make_handler("test", "192.0.2.10", 8443, "ABC123"),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with urlopen(
                    f"http://127.0.0.1:{server.server_port}/status", timeout=2
                ) as response:
                    payload = json.load(response)
                self.assertEqual(payload["bridge_state"], "awaiting_credentials")
                self.assertTrue(payload["transport"]["authentication_required"])
                self.assertTrue(payload["transport"]["certificate_matches_pin"])
                self.assertFalse(payload["commands_enabled"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

