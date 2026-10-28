# HA Vivint Bridge

HA Vivint Bridge is an independent, local-first interoperability research
project for connecting an authorized Vivint security panel to Home Assistant.
The long-term goal is reliable local state, events, and carefully controlled
operations without making Vivint's hosted services the steady-state transport.

> [!IMPORTANT]
> This repository is currently a read-only research bridge, not a finished
> local Vivint integration. It does not currently provide local alarm, lock,
> user, or PIN control.

## Current state

The reference deployment currently uses two separate paths:

```text
Vivint devices
    |
    +-- Vivint hosted services --> ha-vivint --> working Home Assistant entities
    |
    +-- panel-local HTTPS ------> HA Vivint Bridge --> research/status entities
```

The existing [`ha-vivint`](https://github.com/natekspencer/ha-vivint)
integration supplies the functional Home Assistant alarm, lock, camera, and
sensor entities. It is cloud-backed and is not included in this repository.

This project currently provides:

- A containerized research service with `/healthz` and `/status` endpoints.
- A TLS-pinned, unauthenticated probe of the panel-local HTTPS service.
- Explicit reporting of reachability, HTTP authentication state, and
  certificate-pin validation.
- Optional Home Assistant REST entities for bridge health and research status.
- A non-root, read-only container with Linux capabilities dropped.
- A one-time helper for exporting authorized RTSP/media credential material
  without printing secret values.

It does **not** currently provide:

- Authenticated panel-local inventory or event streaming.
- Local alarm arming or disarming.
- Local lock or garage-door control.
- Vivint user, permission, or PIN management.
- A subscription-free replacement for the existing cloud integration.
- A HACS-installable Home Assistant integration.

See [`docs/protocol-status.md`](docs/protocol-status.md) for the verified
findings, exact blocker, and research boundary.

## Research target

The current physical research target is the Vivint VS-SH2000 panel family.
Compatibility with other Vivint panels must not be assumed without physical
validation.

Read-only discovery has confirmed a panel-local TLS service on port 8443 that
requires authentication. The authorized hosted `panel-login` bootstrap was also
tested, but the returned credential material is for RTSP/media access rather
than the panel's HTTPS admin service. It must not be sent to port 8443.

## Quick start

Requirements:

- Docker with Compose support
- An authorized Vivint system on the same trusted LAN
- The panel's LAN address and observed SHA-256 certificate fingerprint

Copy [`.env.example`](.env.example) to `.env` and replace the example values:

```dotenv
VIVINT_PANEL_HOST=192.0.2.10
VIVINT_PANEL_PORT=8443
VIVINT_PANEL_CERT_SHA256=REPLACE_WITH_OBSERVED_SHA256_FINGERPRINT
VIVINT_MODE=research
```

The address above belongs to the documentation-only `192.0.2.0/24` range. Do
not commit a real address, certificate fingerprint, serial number, token, PIN,
or credential file.

Start the bridge and check its status:

```bash
docker compose up --build -d
curl http://localhost:8099/healthz
curl http://localhost:8099/status
```

Do not expose port `8099` to the public internet.

## Home Assistant status entities

[`homeassistant/vivint_bridge_rest.yaml`](homeassistant/vivint_bridge_rest.yaml)
creates entities for:

- Bridge state
- Panel HTTPS status
- Panel reachability
- TLS certificate-pin validation

Place the file beside Home Assistant's `configuration.yaml`, add the following
line, validate the configuration, and restart Home Assistant:

```yaml
rest: !include vivint_bridge_rest.yaml
```

These entities deliberately omit the panel address, certificate fingerprint,
serial number, and device identifiers.

## Media credential helper

[`scripts/bootstrap_media_credentials.py`](scripts/bootstrap_media_credentials.py)
can export authorized `panel-login` credential material from an existing
Home Assistant `ha-vivint` config entry. The helper:

- Writes a new mode-`0600` file atomically.
- Refuses to overwrite an existing output file.
- Prints only the number of panels and returned field names.
- Classifies its output as `rtsp_media`.

The output is sensitive even though it is not an HTTPS admin credential. Store
it outside the repository in a deployment-only secret directory. Do not mount
it into this bridge or send it to port 8443.

## Safety and privacy

This project interacts with a physical security system. Until the authorization
model and protocol are verified:

- Keep all bridge operations read-only.
- Do not guess control routes or authentication payloads.
- Do not factory-reset the panel or change its firmware.
- Do not remove enrolled devices or modify pairing state.
- Do not publish credentials, tokens, PINs, addresses, serial numbers,
  certificate fingerprints, QR codes, or unredacted diagnostics.
- Do not rely on this project for emergency response, life safety, or
  professional alarm monitoring.

If reporting a problem, redact all account, household, panel, and network
identifiers before posting logs or screenshots.

## Roadmap

Development is intentionally staged:

1. Verify an authorized authentication handshake for the panel-local HTTPS
   service.
2. Document and validate read-only inventory schemas.
3. Prove local event streaming and reconnect behavior.
4. Build a native Home Assistant integration around the validated read path.
5. Add narrowly scoped controls with authorization, confirmation, audit logs,
   and failure handling.
6. Consider user and PIN administration only after the underlying write
   protocol and rollback boundaries are understood.

## Related projects and acknowledgements

HA Vivint Bridge is not a fork of these projects and does not vendor their
source code. Their public work and documentation informed the research:

- [`ha-vivint`](https://github.com/natekspencer/ha-vivint) — the maintained,
  cloud-backed Home Assistant integration used by the reference deployment.
- [`vivintpy`](https://github.com/natekspencer/vivintpy) — the Python client
  underlying `ha-vivint` and used by the media credential helper.
- [`Riebart/vivint.py`](https://github.com/Riebart/vivint.py) — earlier Vivint
  API and protocol research, including the RTSP credential finding.
- [`homebridge-vivint`](https://github.com/balansse/homebridge-vivint) — a
  Vivint integration for Homebridge and Apple Home.
- [`VivintOne`](https://github.com/mikezio/vivintone-home-assistant) — a
  separate local-first Vivint platform and Home Assistant development preview.

## Disclaimer

This is an unofficial, independent project. It is not affiliated with,
endorsed by, or supported by Vivint or Home Assistant. Vivint and related marks
belong to their respective owners. Use this software only with systems you own
or are explicitly authorized to administer, and at your own risk.

## License

Licensed under the [MIT License](LICENSE).
