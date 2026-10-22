# Validation record — 0.1.0

By Jason Stys. Measured observations, not operational certification or an independent
human security audit. Original implementation and review are AI-assisted.

## Local core and browser verification

Windows/Python 3.14 local validation passed **67 Python cases** at **99.15% statement
coverage of the report contract**, not native SDK/orchestration coverage. Cases include
exclusive report creation, byte/duplicate-key/finite-value/schema/source/UUID/calendar
bounds, derived outcomes, planned-stop versus crash classification, downloaded/piped
log recovery and actual reference-method dispatch ordering with isolated synthetic
states. Those synthetic unit states are not native flight/integration evidence.

The pure TypeScript validation/filter/graph module passed **36 tests** at **96.87%
statements, 96.15% branches and 100% functions**. The whole UI has no claimed unit
coverage percentage. **12 actual production-viewer browser journeys** passed across
Chromium, Firefox and WebKit: strict file import, false-green rejection, inert hostile
strings, trace filtering, complete JSON download despite view filters, provenance
warning, help/Esc, WCAG axe tags, author/contact links and 390px overflow. No outbound
requests occurred in the hostile-import test. Native-shaped browser inputs are clearly
labeled fixtures and never counted as real native results.

Release C++ kernel assertions, 20,000 seeded malformed inputs, queue/timer/pair-order
oracles and 50,000 forwarding iterations passed locally. One initial MSVC Release
iteration observation was 9,283 microseconds, not a network-throughput SLA or portable
benchmark guarantee. Linux CI also exercises address/undefined sanitizers. C++ does
not claim a measured line-coverage percentage. Production output passed unchanged
50,000-byte JS / 8,000-byte CSS gzip limits. Formatting, strict TS, generated schema,
file/source navigation and source/header checks passed locally.

## Actual native baseline, independently measured

Both actual **PX4 1.16.1 and 1.17.0** jobs passed all eight required scenarios at
framework source `8742ed961e3dc15c4743e7826bfe5fe0e2bb573c` in
[run 39706232209](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/runs/39706232209).
[NATIVE_RESULTS.json](NATIVE_RESULTS.json) records source/executable identity, exact
job IDs, UTC times, checks/metrics/counters, retained counts and scenario labels.

| Observation | PX4 1.16.1 | PX4 1.17.0 |
| --- | ---: | ---: |
| Independently observed minimum delay | 250 ms | 250 ms |
| Packet-order inversions | 534 | 536 |
| Duplicated packet IDs | 829 | 830 |
| Stale age during blackout | 6.168 s | 6.454 s |
| Stored mission items despite unconfirmed upload | 2 | 2 |
| Observed takeoff relative altitude | 3.370 m | 3.223 m |
| Observed low simulated battery | 19% | 17% |
| Owned boots / replayed application commands | 2 / 0 | 2 / 0 |
| Retained per-phase trace records | 661 | 645 |

All eight scenario labels appear in each recovered trace excerpt. Observed disarmed
relative altitudes were -0.369 m and -0.657 m, consistent with simulator estimator bias;
the acceptance requires disarm and an absolute relative altitude within 2 m. Neither
SDK acknowledgements nor successful process exits substitute for observed motion.
Both native dependency audits passed. These are software-in-the-loop observations,
not hardware, real flight or proof of every application/autopilot/transport.

The aggregate baseline workflow above failed only the new browser test's formatting
check, even though both native jobs passed. That formatting defect was corrected and
checked for idempotence; it is not concealed by the native baseline table. The final
changes also enforce stale/reserve/health/armed guards **before** reference SDK calls;
native blackout/low-battery scenarios attempt the actual API and require denial with
an unchanged command count. Every later source revision must obtain its own matching
[Validation](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/validate.yml)
and [CodeQL](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/codeql.yml)
results. Historical numbers are never assumed proof of a changed implementation.

## Failure history and review

- Restricted Windows setup could not read the Visual Studio SDK registry. Normal
  scoped process permissions used the existing compiler; no host installation changed.
- A signed/unsigned C++ comparison was corrected, not suppressed. Release assertions
  remain active and no coverage/time/size threshold was weakened.
- Node's JSON import attribute was added after the first browser setup failure.
  A new chained browser expression needed a second formatter pass; final checks include
  an explicit formatting verification, not an assumption that one write pass suffices.
- The first PX4 1.16.1 attempt failed **before runtime acceptance**: upstream's legacy
  version generator indexed absent NuttX tags in a shallow recursive checkout. The
  workflow now fetches official metadata tags and rechecks unchanged pinned HEAD.
  Upstream source/acceptance oracles were not patched. This was build preparation,
  not observed application/autopilot misbehavior.
- Review added planned-stop/crash distinction, phase-scoped order oracles, retained
  per-phase trace selection and actual pre-SDK dispatch-denial checks. Failure and
  unsupported/not-reached records remain explicit. Earlier failed runs were not deleted.

CodeQL's separate C++ compiler-backed, Python and TypeScript jobs passed without open
findings at review. Locked dependency audits reported no known vulnerabilities at
test time, not a guarantee against future flaws. A benign Node NO_COLOR/FORCE_COLOR
environment warning remains visible; it is not suppressed or counted as a test failure.

## Storage and operational scope

Storage was checked before Actions and again before subsequent validation: 62,959,952
current artifact bytes and 8,185,324,614 separate cache bytes, across 96 then 97 owned
repositories. Billing quota/percentage was unavailable. Nothing was archived/deleted,
and retention/billing policies were not changed. These workflows upload neither
caches nor artifacts; bounded full report JSON remains retrievable in job logs.

No paid resource, real aircraft, serial/radio link, external AI provider, private user
account or host Docker repair was used. The viewer is local-only. Independent human
audit, hardware-in-loop, ArduPilot, production staging/hosting and operational release
approval are **not performed**, not silently marked passed or implemented.
