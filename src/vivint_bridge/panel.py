from __future__ import annotations

import hashlib
import socket
import ssl
from dataclasses import dataclass


@dataclass(frozen=True)
class PanelProbeResult:
    host: str
    port: int
    reachable: bool
    tls: bool
    http_status: int | None = None
    server: str | None = None
    certificate_sha256: str | None = None
    certificate_matches_pin: bool | None = None
    error: str | None = None

    @property
    def authentication_required(self) -> bool:
        return self.http_status in {401, 403}


def normalize_fingerprint(value: str) -> str:
    return "".join(
        character
        for character in value.upper()
        if character in "0123456789ABCDEF"
    )


def _read_headers(connection: ssl.SSLSocket, limit: int = 16_384) -> bytes:
    response = bytearray()
    while b"\r\n\r\n" not in response and len(response) < limit:
        chunk = connection.recv(min(4096, limit - len(response)))
        if not chunk:
            break
        response.extend(chunk)
    return bytes(response)


def _parse_response_headers(data: bytes) -> tuple[int | None, str | None]:
    text = data.decode("iso-8859-1", errors="replace")
    lines = text.split("\r\n")
    status: int | None = None
    server: str | None = None

    if lines:
        parts = lines[0].split(" ", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            status = int(parts[1])

    for line in lines[1:]:
        name, separator, value = line.partition(":")
        if separator and name.lower() == "server":
            server = value.strip() or None
            break

    return status, server


def probe_panel(
    host: str,
    port: int = 8443,
    *,
    timeout: float = 3.0,
    expected_certificate_sha256: str = "",
) -> PanelProbeResult:
    """Probe the panel's TLS service without authenticating or sending a command."""

    expected_pin = normalize_fingerprint(expected_certificate_sha256)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, port), timeout=timeout) as raw_socket:
            with context.wrap_socket(raw_socket, server_hostname=host) as connection:
                certificate = connection.getpeercert(binary_form=True)
                fingerprint = hashlib.sha256(certificate).hexdigest().upper()
                pin_matches = fingerprint == expected_pin if expected_pin else None

                request = (
                    "GET / HTTP/1.1\r\n"
                    f"Host: {host}:{port}\r\n"
                    "User-Agent: ha-vivint-bridge/0.2\r\n"
                    "Accept: text/plain\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii")
                connection.sendall(request)
                status, server = _parse_response_headers(_read_headers(connection))

        return PanelProbeResult(
            host=host,
            port=port,
            reachable=True,
            tls=True,
            http_status=status,
            server=server,
            certificate_sha256=fingerprint,
            certificate_matches_pin=pin_matches,
        )
    except (OSError, ssl.SSLError) as error:
        return PanelProbeResult(
            host=host,
            port=port,
            reachable=False,
            tls=False,
            error=f"{type(error).__name__}: {error}",
        )
