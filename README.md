# HA Vivint Bridge

Local-first bridge research for connecting an authorized Vivint panel to Home
Assistant without making Vivint's hosted API the steady-state transport.

The project is currently a read-only research bridge, not a functioning control
path. It provides a containerized service boundary, health/status endpoints,
and a TLS-pinned probe for the panel-local HTTPS service so protocol work can
proceed without pretending that an unverified endpoint or control path is safe.

## Current status

- The research service runs as a non-root, read-only container with all Linux
  capabilities dropped.
- It performs an unauthenticated `GET /` against a configured panel to verify
  HTTPS reachability, the TLS certificate fingerprint, and the expected
  authentication boundary.
- It performs no panel authentication, inventory reads, writes, enrollment,
  firmware changes, or control commands.
- `GET /healthz` reports whether the research service is alive.
- `GET /status` reports the bridge's blocked state and the exact reason.
- No credentials, serial numbers, access keys, or private panel data belong in
  this repository.

## Authorized account bootstrap finding

The authorized Vivint account bootstrap was exercised successfully. The hosted
`panel-login` response returned credential material, but primary-source protocol
research identifies it as RTSP digest/nonce credentials for panel media access,
not credentials for the panel's HTTPS admin service on port 8443.

[`scripts/bootstrap_media_credentials.py`](scripts/bootstrap_media_credentials.py)
exports that media-only material to a new mode-0600 file while printing only its
structure. Its output belongs in a deployment secret store outside Git. Do not
mount it into this bridge or send it to port 8443.

The full research boundary and next milestone are in
[`docs/protocol-status.md`](docs/protocol-status.md).

## Run locally

```bash
docker compose up --build -d
curl http://localhost:8099/healthz
curl http://localhost:8099/status
```

The panel-specific values belong in a deployment-only `.env` file, never in
Git:

```dotenv
VIVINT_PANEL_HOST=192.0.2.10
VIVINT_PANEL_PORT=8443
VIVINT_PANEL_CERT_SHA256=REPLACE_WITH_OBSERVED_SHA256_FINGERPRINT
VIVINT_MODE=research
```

## Home Assistant status entities

The optional [`homeassistant/vivint_bridge_rest.yaml`](homeassistant/vivint_bridge_rest.yaml)
file creates local Home Assistant entities for bridge state, panel reachability,
the panel's HTTP authentication boundary, and TLS pin validation. It deliberately
does not publish the panel address, certificate fingerprint, or device identifiers
as entity attributes.

Add this line to Home Assistant's `configuration.yaml`, place the included YAML
file beside it, validate the configuration, and restart Home Assistant:

```yaml
rest: !include vivint_bridge_rest.yaml
```

## Safety boundary

Development must remain read-only until the exact VS-SH2000 local transport and
authorization model are verified. Do not factory-reset the panel, alter its
firmware, remove enrolled devices, derive or publish credentials, or send
guessed control calls.

## Intended architecture

```text
Vivint sensors and Z-Wave devices
              |
              v
      Vivint VS-SH2000 panel
              |
       verified local protocol
              |
              v
       HA Vivint Bridge
              |
      versioned local API/MQTT
              |
              v
        Home Assistant
```

