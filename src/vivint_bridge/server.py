import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .panel import PanelProbeResult, probe_panel


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


def _bridge_state(panel_host: str, probe: PanelProbeResult | None) -> str:
    if not panel_host:
        return "panel_not_configured"
    if probe is None or not probe.reachable:
        return "panel_unreachable"
    if probe.certificate_matches_pin is False:
        return "certificate_mismatch"
    if probe.certificate_matches_pin is None:
        return "certificate_unpinned"
    if probe.authentication_required:
        return "awaiting_credentials"
    return "protocol_unverified"


def _blocker(panel_host: str, probe: PanelProbeResult | None) -> str:
    state = _bridge_state(panel_host, probe)
    if state == "panel_not_configured":
        return "The Vivint panel host has not been configured."
    if state == "panel_unreachable":
        return "The configured Vivint panel local HTTPS service is not reachable."
    if state == "certificate_mismatch":
        return "The panel TLS certificate does not match the configured fingerprint pin."
    if state == "certificate_unpinned":
        return (
            "The panel is reachable, but its TLS certificate fingerprint has "
            "not been pinned in the deployment configuration."
        )
    if state == "awaiting_credentials":
        return (
            "The authenticated panel-local HTTPS service is reachable. "
            "Panel credentials and read-only inventory/event routes have not yet "
            "been provisioned and validated."
        )
    return (
        "The panel responded, but the response is not yet a validated Vivint "
        "local protocol state."
    )


def status_payload(
    mode: str,
    panel_host: str,
    panel_port: int = 8443,
    panel_probe: PanelProbeResult | None = None,
) -> dict[str, Any]:
    return {
        "service": "vivint-local-bridge",
        "version": "0.2.0-research",
        "mode": mode,
        "panel_host_configured": bool(panel_host),
        "panel_host": panel_host or None,
        "bridge_state": _bridge_state(panel_host, panel_probe),
        "transport": {
            "service": "_vivint-admin._tcp.local",
            "scheme": "https",
            "port": panel_port,
            "reachable": panel_probe.reachable if panel_probe else False,
            "tls": panel_probe.tls if panel_probe else False,
            "http_status": panel_probe.http_status if panel_probe else None,
            "authentication_required": (
                panel_probe.authentication_required if panel_probe else None
            ),
            "server": panel_probe.server if panel_probe else None,
            "certificate_sha256": (
                panel_probe.certificate_sha256 if panel_probe else None
            ),
            "certificate_matches_pin": (
                panel_probe.certificate_matches_pin if panel_probe else None
            ),
            "error": panel_probe.error if panel_probe else None,
        },
        "device_inventory": [],
        "commands_enabled": False,
        "blocker": _blocker(panel_host, panel_probe),
        "safety": {
            "panel_writes": False,
            "firmware_changes": False,
            "factory_reset": False,
        },
        "checked_at": now_utc(),
    }


def make_handler(
    mode: str,
    panel_host: str,
    panel_port: int = 8443,
    expected_certificate_sha256: str = "",
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "VivintLocalBridgeResearch/0.2"

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
                panel_probe = None
                if panel_host:
                    panel_probe = probe_panel(
                        panel_host,
                        panel_port,
                        expected_certificate_sha256=expected_certificate_sha256,
                    )
                self._send_json(
                    200,
                    status_payload(mode, panel_host, panel_port, panel_probe),
                )
                return

            if self.path == "/":
                self._send_json(
                    200,
                    {
                        "service": "vivint-local-bridge",
                        "message": (
                            "Read-only research bridge is running; see /status "
                            "for the panel transport state."
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
    panel_port = int(os.environ.get("VIVINT_PANEL_PORT", "8443"))
    expected_certificate_sha256 = os.environ.get(
        "VIVINT_PANEL_CERT_SHA256", ""
    ).strip()
    mode = os.environ.get("VIVINT_MODE", "research")
    server = ThreadingHTTPServer(
        ("0.0.0.0", listen_port),
        make_handler(
            mode,
            panel_host,
            panel_port,
            expected_certificate_sha256,
        ),
    )
    print(f"Vivint bridge research service listening on {listen_port}", flush=True)
    server.serve_forever()

