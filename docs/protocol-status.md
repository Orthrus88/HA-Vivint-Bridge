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

## Exact blocker

The missing component is a public, reviewable implementation of the
VS-SH2000's authenticated LAN service registry, event subscription, device
mapping, and safe command protocol. Without that implementation—or verified
observations from this exact panel family—adding endpoints or commands would be
guesswork.

## Safe next milestone

1. Record the exact VS-SH2000 hardware revision and firmware version.
2. Identify its LAN address without modifying the panel.
3. Perform a read-only TCP/TLS/service inventory from the authorized local
   network.
4. Capture only non-secret service metadata needed to distinguish HTTPS, SSE,
   RTSP, or another transport. Never commit credentials, keys, serial numbers,
   QR codes, or account data.
5. Implement a read-only transport adapter behind an interface with recorded
   fixtures and tests.
6. Prove inventory and live sensor events before considering any write/control
   path.

## References

- Home Assistant community thread: https://community.home-assistant.io/t/vivint-integration/110667/3
- `ha-vivint`: https://github.com/natekspencer/ha-vivint
- `vivintpy`: https://github.com/natekspencer/vivintpy
- Homebridge Vivint: https://github.com/balansse/homebridge-vivint
- VivintOne Home Assistant adapter: https://github.com/mikezio/vivintone-home-assistant
- VivintOne local sensor transport notes: https://github.com/mikezio/vivintone-home-assistant/blob/main/docs/local-sensor-events.md
- VivintOne compatibility notes: https://github.com/mikezio/vivintone-home-assistant/blob/main/docs/compatibility.md

