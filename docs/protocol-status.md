# Protocol status and research boundary

Status date: 2026-10-28

## Finding

No ready, open, subscription-free local bridge is currently available for the
Vivint VS-SH2000 panel used by this project.

## Evidence

1. The Home Assistant community thread's Homebridge route explicitly reports
   that it requires Vivint service and does not work standalone.
2. The current `ha-vivint` integration is built on `vivintpy`. That library
   models Vivint devices through the reverse-engineered Vivint Sky API and uses
   PubNub for hosted real-time events.
3. `@balansse/homebridge-vivint` requires Vivint authentication/MFA to create a
   refresh token and periodically renews its hosted API session and snapshot.
4. VivintOne is the first credible panel-local architecture found. It documents
   panel-local HTTPS inventory and a long-lived server-sent-event stream for
   supported sensor/security state.
5. VivintOne is still a development preview, device controls are disabled, and
   its public repository contains only the Home Assistant adapter. Its native
   core, provisioning flow, and protocol implementation are intentionally not
   public.
6. VivintOne's published physical validation covers Smart Hub Pro Gen 2
   (`imx8mm-yellowstone`), not the older VS-SH2000 family used here. It may also
   require an authorized Vivint account during initial enrollment even when the
   supported steady-state event path is local.

## Verified on this VS-SH2000 family

Read-only LAN discovery confirmed that the panel advertises both
`_vivint-admin._tcp.local` and `_ssh._tcp.local` over mDNS. The admin service is
TLS on port 8443, presents a self-signed certificate with subject
`CN=vivint.panel`, identifies as Python/aiohttp, and requires authentication.
The SSH service was not accessed. Device-specific addresses, serial numbers,
and certificate fingerprints are intentionally excluded from this repository.

The maintained `vivintpy` client also documents an authenticated hosted
`panel-login/{panel_id}` endpoint that returns panel-local credentials. That is
evidence for an authorized bootstrap path, but it has not yet been exercised in
this project.

## Exact blocker

The missing component is the authenticated route and schema map for the
VS-SH2000's LAN service registry, event subscription, device mapping, and safe
command protocol. The transport and authentication boundary are now verified;
inventory and event routes still must be observed using authorized credentials
before any control endpoint is considered.

## Safe next milestone

1. Obtain panel-local credentials through the authorized account bootstrap and
   store them only in the deployment secret store.
2. Identify the read-only inventory and event routes without sending control
   calls.
3. Record redacted response fixtures and implement schema validation.
4. Prove inventory and live sensor events before considering any write/control
   path.
5. Add explicit authorization, audit logging, confirmation, and rollback
   boundaries before user, PIN, lock, or alarm mutations.

## References

- Home Assistant community thread: https://community.home-assistant.io/t/vivint-integration/110667/3
- `ha-vivint`: https://github.com/natekspencer/ha-vivint
- `vivintpy`: https://github.com/natekspencer/vivintpy
- Homebridge Vivint: https://github.com/balansse/homebridge-vivint
- VivintOne Home Assistant adapter: https://github.com/mikezio/vivintone-home-assistant
- VivintOne local sensor transport notes: https://github.com/mikezio/vivintone-home-assistant/blob/main/docs/local-sensor-events.md
- VivintOne compatibility notes: https://github.com/mikezio/vivintone-home-assistant/blob/main/docs/compatibility.md

