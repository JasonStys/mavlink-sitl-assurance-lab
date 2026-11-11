# Offline desktop application candidate — 10 November 2026

This is a **local uncommitted 0.2.0 candidate**, not a published release or a
hosted CI pass. Its last committed baseline is
`330198e7c2ed997343bf90fcb84faaf00faa705f`; package metadata explicitly records
`source_dirty: true`. The baseline commit does not identify the subsequent
uncommitted implementation. A clean committed build and hosted validation are
required before any release publication.

## Useful application workflow

The executable opens this project's full offline evidence viewer. A reviewer can
import any valid supported JSON, filter outcomes, inspect expected and observed
checks and retained packet metadata, then export the original validated report
and the derived packet review. Optional examples remain within this application.
There is no separate demo executable and no report-upload or simulator endpoint.

The new native controls authenticate only the launch they belong to. A private
ephemeral token moves from the initial address fragment into memory and the
fragment is removed before status requests. Quit requires the exact bound
loopback authority, same browser origin, private token and exact confirmation.
A second app launch has a separate port/token. The console Ctrl+C fallback stays
available; closing a tab alone does not stop the service.

## Observed validation

| Check | Observed result and denominator |
| --- | --- |
| Python | 153 tests passed on Python 3.14.10; 98.53% statement coverage for `assurance`, preserving the 90% floor and existing explicit `native.py`/`runner.py` exclusions. |
| TypeScript | 53 tests passed. Existing report/delivery coverage: 97.70% statements, 96.66% branches, 100% functions, 99.13% lines. Fragment parsing tests and the real compiled GUI separately cover the new desktop path; it is not silently added to the existing utility coverage denominator. |
| Windows C++ | The original MSVC core suite passed: seeded 20,000 malformed cases and 50,000 measured packets; bounded queue and independent kernel oracles passed. This is not PX4 or relay integration execution. |
| Production viewer | All 15 Chromium/Firefox/WebKit journeys passed on a separate test-only port with no server reuse, including hostile text, rejected false-green input, guide, accessibility and narrow layout. |
| Actual portable application | A new Windows ZIP was safely extracted into a fresh unrelated directory. Its actual executable passed readiness/metadata/nonce checks, custom JSON import, failed-case filtering, exact report export, packet-review export and malformed-import retention. Developer runtimes were removed from PATH; no source server was used. |
| Native accessibility and lifecycle | Populated compiled UI passed WCAG 2 A/AA, 2.1 AA and 2.2 AA Axe rules, 390-pixel layout and empty browser storage checks. Cancelled Quit left the app usable; keyboard-confirmed Quit returned process exit 0, closed its output pipe and left the service unreachable. No forced cleanup was needed. |
| Security negatives | Actual HTTP tests reject foreign Host/Origin, missing/wrong/cross-instance token, malformed Quit, arbitrary report POST and unknown path traversal. Package guards reject stale version declarations, dirty CI builds and archive escape/alias cases. |
| Source and supply chain | Ruff, TypeScript build, canonical schema, source/file navigation and repository privacy/output gates passed. Existing gzip budgets remain 50,000 JS / 8,000 CSS bytes; observed production output was 11,935 / 1,424 bytes. Live packaging-only pip audit and locked npm audit reported no known vulnerabilities on this date. |

The independent imported example used relay ID 77, receive time 100 ms and send
time 140 ms, so the expected local delay was exactly 40 ms. The downloaded review
contained `[40]`, the full report download equaled the imported report, and an
invalid subsequent import preserved that same prior validated report. The report
remained explicitly synthetic; neither its source pin nor an imported native claim
became provenance attestation.

The accepted local candidate ZIP SHA256 was
`aeecc070c59ddb9f6ff048d9ad435ed3c9ebf653f387bb0a83972b40ee8d8102`.
Its source is deliberately dirty/unreleased. Its executable was used from the
extracted archive, not a source tree or pre-existing server. Two actual UI PNGs
were individually inspected at original resolution; public illustrated editions
remain a separately coordinated publication step.

## Corrections and remaining boundaries

The first build exposed PyInstaller resolving relative data paths against the
spec directory. Inputs now use absolute controlled paths. The first native launch
also exposed a locale-dependent Windows banner byte in redirected output; its
startup/readiness banner now uses ASCII. The prior failed candidate remains
private, has no success checksum sidecar and was not published. No fallback or
retry was added to turn a failing test green.

An earlier functional checkpoint used Python 3.14.6 and ZIP
`7b93d7c4c5059d243ccb10124602afe45222e387dabfa0e18c2233db6adde16f`.
It is retained only as private historical evidence. The current candidate was
rebuilt with the isolated official Python 3.14.10 SDK. Its actual bundled
`python314.dll` reports version 3.14.10 and its SHA256 matches the SDK DLL.
Metadata records `python_version`, runtime loading checks it, the native workflow
pins 3.14.10 with a fresh lookup, and the builder actively rejects older freezes.

The three-OS desktop workflow has been added but **has not been run remotely in
this local phase**. Existing Linux PX4 1.16.1/1.17.0 integration jobs are unchanged
and were not executed on this PC. The Windows viewer does not bundle PX4, MAVSDK
or the Linux relay, cannot operate an aircraft, and performs no live network
simulation. No Docker or real user data was used.

These are unsigned portable candidates, not signed installers or a proven
clean-system install/upgrade/uninstall transaction. The automated native journey
used `--no-browser` with headless Chromium; normal OS browser opening and Desktop
shortcuts remain separate manual acceptance. The trusted local OS can inspect
active browser memory. Packet timing is local relay evidence, not a receiver ACK,
CRC/signature proof or assurance of flight safety.
