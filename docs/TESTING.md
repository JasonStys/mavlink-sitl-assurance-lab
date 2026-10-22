# Test strategy and known gaps

By Jason Stys. Test requirements and expected observations independently of production
status messages; preserve failures and distinguish each evidence layer.

| Risk | Check and oracle |
| --- | --- |
| Packet truncation/signing-length/ID bugs | Independent v1/v2 concatenated/truncated fixtures, unsupported flags, seeded malformed corpus; actual native traffic separately. |
| Release tests disappear with NDEBUG | Custom throwing C++ check function; every oracle executes in Release. |
| Timing/queue/order defects | Injected logical time, 249/250 ms boundaries, pair order and odd-packet expiry, bounded overflow and profile-purge checks. |
| Memory/undefined behavior | Address/undefined sanitizers on authored C++ in Linux core CI; deterministic malformed corpus. |
| Native policy falsely claims a fault happened | Correlate receive/send relay-local IDs and inspect actual dropped ACKs independently of aggregate counters. |
| Command acknowledgement mistaken for motion | Observe native altitude/mode/armed takeoff, HOLD, landing/disarm. |
| Stale link or low reserve treated as safe | Exact finite dispatch boundaries, actual disconnected blackout recovery and actual simulator battery drain. |
| A denial merely reported but not enforced | Isolated actual reference-method ordering tests plus native API start attempts during blackout/low reserve; no SDK command/counter effect is allowed. |
| Restart repeats application commands | Grounded restart, expired old SDK connection, new SDK session and observed grounded state; reference-client command count remains zero. |
| False green/missing/unsupported report | Exact scenario set, duplicate-name rejection, derived status, source pin/hash and negative envelope tests. |
| Unsafe import/export | Byte/depth/node limits, duplicate JSON keys, text-only hostile strings, rejected contradictory imports and exclusive report creation. |
| UI usability/privacy | Real production viewer in Chromium/Firefox/WebKit; actual file picker and download, modal Esc, WCAG axe tags, 390px overflow, no outbound requests. |
| Drift/unsafe delivery | Generated serialization/file/source checks, strict TS, style, pinned Actions, unchanged size gates, three-language CodeQL and locked dependency audits. |

Python coverage >=90% statements covers **assurance/report.py**, not SDK/orchestration
modules. Those modules must pass separate actual native jobs; no mock substitution.
The browser utility has >=90% statements/lines/functions and >=80% branches; actual
UI behavior is browser-tested rather than misrepresented as whole-UI unit coverage.
C++ does not claim a measured coverage percentage. It has independent Release oracles,
sanitizers, native integration and a seeded 20,000-case malformed corpus. This is
not exhaustive fuzzing, mutation coverage, formal verification or hardware testing.

The 50,000-packet C++ observation reports elapsed microseconds and bounded queue size.
No cross-host throughput SLA is enforced. JS/CSS gzip budgets are 50,000/8,000 bytes;
missing build output fails instead of appearing as a zero-byte success.

Both exact PX4 versions must build and pass all eight actual scenarios. Every failure
produces a failed record, while later unexecuted cases remain unsupported/not reached.
Actual failed-call timeouts are not silently converted into "expected failure" if the
underlying native operation has not resolved. Unexpected cleanup failure invalidates
a green run. No current assertion/coverage/size threshold should be weakened to pass.

Known gaps: ArduPilot, additional applications/vehicles, serial/RF links, signed-message
and encrypted-link verification, high-rate link modeling, hardware-in-loop, malicious
local OS protection, real flight, operational privacy, manual screen-reader speech
output/usability studies, production hosting and signed report provenance. Nothing
in the test results authorizes real flight, legal operation or safety certification.
