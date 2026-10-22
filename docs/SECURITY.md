# Threat model and privacy limits

By Jason Stys. This is not a certified secure network product or operational flight system.

Assets: a trusted isolated host, simulator-only command authority, evidence integrity,
private report contents and bounded resource use. Trust the installed toolchain/OS,
official pinned upstream/dependency sources and original lab source. Do not trust
uploaded JSON, packet bytes, absence of traffic, a green UI alone or a report's claim
of native provenance.

| Threat | Implemented boundary | Remaining limitation |
| --- | --- | --- |
| Accidental real/unowned attachment | No endpoint arguments; unused-port check; fixed loopback peers; owned process and source/executable identity. | A malicious OS/local proxy can race or impersonate loopback; hashes are not attestation. |
| Arbitrary executable/input injection | No executable plugins, raw shell input, remote IP or user-selected binary. Control vocabulary/duration/ASCII are bounded. | Reviewed local source/toolchain is trusted and runs with the user's permissions. |
| Queue/resource exhaustion | 2048-byte datagrams, 256 pending entries, counted overflow, one-minute faults and fifteen-minute relay watchdog. | External SDK/OS/autopilot resource behavior is not covered by the kernel bound. |
| False green or ambiguous state | Eight unique scenarios, recomputed outcome, failed/partial visibility, actual observations and source-linked logs. | A malicious author can forge a well-formed report; schema is not provenance authentication. |
| Malicious report/HTML | Local bounded strict JSON; duplicate/depth/node checks; reviewed static schema; textContent DOM; strict CSP; no eval. | Browser/OS vulnerabilities and malicious extensions remain outside this lab. |
| Report exfiltration/tracking | No upload API, analytics, external map/fonts, AI provider, localStorage or accounts. Explicit local download only. | Author-supplied report metadata may itself be private; OS/browser administrators can access local data. |
| Concealed protocol weakness | Framing fields explicitly unverified; no claim that signing encrypts traffic or that loopback authenticates a device. | CRC/signature verification/encryption and real-link security are not implemented. |

The viewer's CSP forbids external resources, frames, form submission and dynamic
script evaluation. Static preview also sends frame-ancestor and nosniff headers.
This is not a system-wide ad blocker or a promise that an untrusted host cannot
modify source/served files. Author/contact links are ordinary explicit navigation,
not automatic outbound requests. No credentials or real-user profiles are collected.

Protocol traces store header metadata, direction, length, policy and relay-local
packet IDs—not raw payload bytes. Cumulative counts remain separate from the bounded
excerpt. Real/unknown packet IDs are not identity, CRC, signing or confidentiality
proof. Generated local runtime data, SDK packages, logs and dependencies are ignored.
The small secret-pattern gate is not exhaustive secret scanning; public diff review
and CodeQL/dependency checks complement it without guaranteeing absence of all flaws.

Run only as an unprivileged trusted local user or isolated CI worker. No sudo runtime,
Docker repair, firewall change, radio, hardware control or cloud account is required.
Source/download dependencies retain upstream licenses; no employer/customer materials,
real incident data, private flight logs, face recognition or person tracking are included.
