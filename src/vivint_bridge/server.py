import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def health_payload(mode: str) -> dict[str, Any]:
    return {
        "service": "vivint-local-bridge",
        "service_health": "ok",
        "bridge_state": "blocked",
        "mode": mode,
        "checked_at": now_utc(),
    }


def status_payload(mode: str, panel_host: str) -> dict[str, Any]:
    return {
        "service": "vivint-local-bridge",
        "version": "0.1.0-scaffold",
        "mode": mode,
        "panel_host_configured": bool(panel_host),
        "panel_host": panel_host or None,
        "bridge_state": "blocked",
        "transport": None,
        "device_inventory": [],
        "commands_enabled": False,
        "blocker": (
            "No public, validated local protocol implementation is available "
            "for the Vivint VS-SH2000 panel. VivintOne's public repository "
            "contains only its Home Assistant adapter; its native core, "
            "provisioning, and protocol implementation are not public, and its "
            "published physical validation covers Smart Hub Pro Gen 2."
        ),
        "safety": {
            "panel_writes": False,
            "firmware_changes": False,
            "factory_reset": False,
        },
        "checked_at": now_utc(),
    }


def make_handler(mode: str, panel_host: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "VivintLocalBridgeScaffold/0.1"

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/healthz":
                self._send_json(200, health_payload(mode))
                return

            if self.path == "/status":
                self._send_json(200, status_payload(mode, panel_host))
                return

            if self.path == "/":
                self._send_json(
                    200,
                    {
                        "service": "vivint-local-bridge",
                        "message": (
                            "Bridge scaffold is running; panel protocol work is "
                            "blocked."
                        ),
                        "endpoints": ["/healthz", "/status"],
                    },
                )
                return

            self._send_json(404, {"error": "not_found"})

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"{self.address_string()} - {fmt % args}", flush=True)

    return Handler


def main() -> None:
    listen_port = int(os.environ.get("LISTEN_PORT", "8099"))
    panel_host = os.environ.get("VIVINT_PANEL_HOST", "").strip()
    mode = os.environ.get("VIVINT_MODE", "scaffold")
    server = ThreadingHTTPServer(
        ("0.0.0.0", listen_port), make_handler(mode, panel_host)
    )
    print(f"Vivint bridge scaffold listening on {listen_port}", flush=True)
    server.serve_forever()

