# HA Vivint Bridge

Local-first bridge research for connecting an authorized Vivint panel to Home
Assistant without making Vivint's hosted API the steady-state transport.

The project is currently an honest scaffold, not a functioning panel bridge.
It provides a containerized service boundary, health/status endpoints, and a
documented protocol blocker so panel work can proceed without pretending that
an unverified endpoint or control path is safe.

## Current status

- The scaffold runs as a non-root, read-only container with all Linux
  capabilities dropped.
- It performs no panel discovery, authentication, reads, writes, enrollment,
  firmware changes, or control commands.
- `GET /healthz` reports whether the scaffold service is alive.
- `GET /status` reports the bridge's blocked state and the exact reason.
- No credentials, serial numbers, access keys, or private panel data belong in
  this repository.

The full research boundary and next milestone are in
[`docs/protocol-status.md`](docs/protocol-status.md).

## Run locally

```bash
docker compose up --build -d
curl http://localhost:8099/healthz
curl http://localhost:8099/status
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

