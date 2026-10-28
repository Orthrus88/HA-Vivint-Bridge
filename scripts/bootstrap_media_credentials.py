"""Export authorized Vivint RTSP/media credentials without printing secrets.

Vivint's hosted ``panel-login`` response contains RTSP digest/nonce material
for the panel's media service. It is not an HTTPS admin credential and must not
be sent to the panel's port 8443 service. This helper is intended to run once
inside Home Assistant after the temporary ``ha-vivint`` config flow completes.
Keep the output in a deployment-only secret store and never add it to Git.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def find_vivint_entry(storage: dict[str, Any]) -> dict[str, Any]:
    """Return the single Vivint config entry from Home Assistant storage."""
    entries = [
        entry
        for entry in storage.get("data", {}).get("entries", [])
        if entry.get("domain") == "vivint"
    ]
    if len(entries) != 1:
        raise RuntimeError(f"Expected one Vivint config entry; found {len(entries)}")
    return entries[0]


def write_secret_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically create a mode-0600 JSON secret without overwriting a file."""
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing secret: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


async def export_media_credentials(config_path: Path, output_path: Path) -> None:
    """Exchange the stored refresh token for RTSP/media credentials."""
    from vivintpy.account import Account

    storage = json.loads(config_path.read_text(encoding="utf-8"))
    entry = find_vivint_entry(storage)
    data = entry.get("data", {})

    username = data.get("username")
    refresh_token = data.get("refresh_token")
    if not username or not refresh_token:
        raise RuntimeError("Vivint config entry is missing username or refresh token")

    account = Account(
        username=username,
        password="refresh-token-only",
        refresh_token=refresh_token,
    )
    exported_panels: list[dict[str, Any]] = []
    try:
        await account.connect(load_devices=True)
        for system in account.systems:
            for panel in system.alarm_panels:
                credentials = await panel.get_panel_credentials()
                exported_panels.append(
                    {
                        "panel_id": panel.id,
                        "partition_id": panel.partition_id,
                        "credentials": credentials,
                    }
                )
    finally:
        await account.disconnect()

    if not exported_panels:
        raise RuntimeError("Vivint account returned no alarm panels")

    write_secret_json(
        output_path,
        {
            "schema_version": 1,
            "credential_purpose": "rtsp_media",
            "panels": exported_panels,
        },
    )

    # Report structure only. Secret values and device identifiers stay silent.
    credential_keys = sorted(
        {
            key
            for panel in exported_panels
            for key in panel["credentials"].keys()
        }
    )
    print(
        json.dumps(
            {
                "panels_exported": len(exported_panels),
                "credential_keys": credential_keys,
                "credential_purpose": "rtsp_media",
                "output_mode": "0600",
            }
        )
    )


def main() -> None:
    """Run the one-time media credential export."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("/config/.storage/core.config_entries"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/config/.vivint-media-bootstrap.json"),
    )
    arguments = parser.parse_args()
    asyncio.run(export_media_credentials(arguments.config, arguments.output))


if __name__ == "__main__":
    main()
