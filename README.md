# MAVLink SITL Assurance Lab

[![Validation](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/validate.yml/badge.svg)](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/validate.yml)
[![CodeQL](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/codeql.yml/badge.svg)](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/workflows/codeql.yml)

**Faults are inputs. Evidence is the output.** An independent compatibility and
reliability lab by [Jason Stys](https://github.com/JasonStys), using actual PX4 SIH,
the native MAVSDK library, a byte-preserving C++ fault relay, Python assertions and
a TypeScript evidence viewer. It tests a reference drone-software interface rather
than merely animating a drone or trusting a process exit code.

This is original, AI-assisted engineering portfolio work. It is **simulator-only**,
not flight software, a ground station, a weapon system or proof of operational
readiness. It cannot accept a real-aircraft endpoint, remote IP, radio, arbitrary
executable or downloaded DUT plugin. No real flight or paid cloud deployment occurs.

## What it demonstrates

- **Two-version compatibility:** source-pinned PX4 **1.16.1** and **1.17.0**, each
  independently built and tested with native MAVSDK **4.0.6**. ArduPilot is explicitly
  **not implemented or validated**, not a skipped test presented as a pass.
- **Native C++ fault injection:** fixed loopback peers, packet blackout, 250 ms
  delay, pair reordering, duplication and selective downstream mission-ACK loss.
  Datagram contents stay unchanged. Timers, packet lengths, queue capacity and
  process lifetime are bounded; overflow is counted, never silently hidden.
- **Independent recovery oracles:** correlate relay-local packet IDs to actual
  receive/send events; observe stale link denial and fresh recovery; inspect an
  unconfirmed mission upload before an explicit new upload; observe actual
  takeoff, HOLD, return/disarm, low battery and an owned autopilot restart.
- **Honest failure reports:** every scenario has expected/observed results, a
  classification, duration and metrics. A failed case dominates the summary;
  unreached/unsupported cases are not green. Source/executable identity, retained
  telemetry, cumulative counters and timestamped packet metadata accompany results.
- **Private local review:** responsive TypeScript UI, outcome filters, case details,
  graph/text observations, trace excerpts, help and JSON download. Reports are read
  in the browser tab, not uploaded, persisted to browser storage or sent to an AI API.
- **Delivery assurance:** multi-OS C++/Python/TypeScript checks, sanitizer-instrumented
  C++, three browser engines, dependency audits and compiler-backed C++ plus
  Python/TypeScript CodeQL. Actions caches and artifact uploads are disabled.

## Quick start: evidence viewer

Requires Node.js **24** and npm. From a fresh clone:

```sh
git clone https://github.com/JasonStys/mavlink-sitl-assurance-lab.git
cd mavlink-sitl-assurance-lab
npm ci --ignore-scripts
npm run build
npm run preview
```

Open **http://127.0.0.1:8851/** and choose **Load synthetic example**. The conspicuous
synthetic label means those values are teaching data, **not an executed native run**.
Import a report produced by the native suite to inspect actual evidence. The viewer
also labels native claims as self-reported: JSON/schema checks are not provenance
attestation. Verify the source-linked CI log and build identity yourself.

No account, password, external map, GPU, Docker or cloud subscription is needed.
The static viewer is not an application backend. It never sends commands to PX4.
Do not expose the development/preview server publicly or open a downloaded report
as executable HTML. Use the controlled file picker. Stop the server with Ctrl-C.

## Native matrix and eight required scenarios

| PX4 release | Verified source identity required by the launcher |
| --- | --- |
| 1.16.1 | `94cb2012792b2ae89f0b147cfee53ee31ae550be` |
| 1.17.0 | `d6f12ad1c4f70ad3230afd7d86e971421e02fef4` |

| Scenario | Independent expected behavior |
| --- | --- |
| Delay | Match receive/send IDs and observe >=240 ms delay for the 250 ms policy; recover fresh telemetry. |
| Reorder | Observe actual packet-order inversions while the reference client remains usable. |
| Duplicate | Observe repeated delivery of the same relay-local ID without losing usable state. |
| Blackout | Lose six seconds of traffic; observe stale/disconnected state, block dispatch and recover without command replay. |
| Interrupted upload | Lose real downstream mission ACKs; confirmed success must not be reported. Inspect stored mission, then explicitly re-upload. |
| Nominal mission | Observe native upload, armed takeoff >3 m, HOLD, return/landing and disarm—not just command acknowledgements. |
| Low battery | Change actual PX4 simulator battery parameters; observe <25% reserve and deny dispatch in the independent reference gate. |
| Autopilot restart | Stop only the owned process, expire the old connection, create a new SDK session and observe fresh grounded state without replay. |

Native execution requires an **isolated, authorized Linux development host** or the
provided GitHub-hosted jobs. Leave other host services and Docker installations
unchanged. Follow [OPERATIONS](docs/OPERATIONS.md) for the fixed checkout/build path,
dependencies, fresh-workspace requirements, logs, recovery and teardown.

```sh
python -m venv .venv
# Windows: .venv/Scripts/Activate.ps1; Linux/macOS: source .venv/bin/activate
python -m pip install --require-hashes -r requirements-native.lock
cmake -S . -B .runtime/build -DCMAKE_BUILD_TYPE=Release
cmake --build .runtime/build --parallel 2
# After the exact upstream checkout and px4_sitl_default build described in OPERATIONS:
python -m assurance.runner --version 1.17.0
```

Every native run writes a **new** `.runtime/report-VERSION.json` and refuses to
overwrite previous evidence. Full marker-delimited JSON and a compact
`NATIVE_ACCEPTANCE` record also appear in Actions job logs. Download one job's plain
text log through GitHub, then recover the viewer file without executing its contents:

```sh
python tools/extract_report.py downloaded-job.log .runtime/recovered-report.json
```

Native and browser integration are separate: browser journeys use synthetic
fixtures; actual autopilot jobs exercise the compiled relay and native SDK directly.
There is no mock fallback when the native build, SDK, simulator or assertion fails.

## Verify locally

Python 3.12–3.14, Node 24 and a C++20 compiler/CMake >=3.25 are supported for core
checks. Only the UDP relay/native autopilot integration is Linux-specific.

```sh
python -m pip install --require-hashes -r requirements.lock
npm ci --ignore-scripts
python -m ruff check assurance tests tools
python -m ruff format --check assurance tests tools
python tools/schema.py --check
python tools/docs_index.py --check
python -m pytest --cov=assurance --cov-report=term-missing
cmake -S . -B .runtime/build -DCMAKE_BUILD_TYPE=Release
cmake --build .runtime/build --config Release --parallel 2
ctest --test-dir .runtime/build -C Release --output-on-failure -V
npm run format:check
npm test
npm run build
python tools/check_repo.py --dist
npx playwright install chromium firefox webkit
npm run test:e2e
npm run audit
python -m pip_audit --disable-pip --no-deps -r requirements.lock
```

C++ assertions stay active in Release/NDEBUG. A seeded malformed corpus and bounded
throughput observation complement independent policy oracles; this is not exhaustive
fuzzing or a universal performance claim. Python's >=90% coverage gate covers the
report contract, not native adapters. The viewer's pure validation/graph utility has
separate coverage gates; browser tests exercise actual production UI behavior.
See [TESTING](docs/TESTING.md) and [VALIDATION](docs/VALIDATION.md).

## Structure and major responsibilities

| File / directory | Responsibility |
| --- | --- |
| `native/fault.hpp`, `native/fault.cpp` | Clock/socket-independent framing metadata, bounded deterministic fault policies and counters. |
| `native/core_tests.cpp` | Release-active independent oracles, malformed corpus and throughput observation. |
| `native/relay.cpp` | Linux fixed-loopback socket, bounded stdin control, actual packet delivery and metadata trace. |
| `assurance/report.py` | Finite evidence schema, outcome consistency, independent dispatch gate and exclusive report I/O. |
| `assurance/native.py` | App-owned simulator/relay, native SDK reference client and cleanup; no arbitrary attachment. |
| `assurance/runner.py` | Eight genuine scenario oracles and classified failure/report orchestration. |
| `ui/src/report.ts` | Strict JSON/duplicate-key checks, reviewed generated-schema subset interpreter and graph/filter helpers. |
| `ui/src/main.ts`, `ui/src/style.css` | Accessible local evidence viewer and responsive presentation. |
| `ui/schema/`, `examples/` | Deterministic serialization schema and explicitly synthetic example. |
| `tests/` | Independent report/extraction tests and production browser journeys. |
| `tools/` | Schema/fixture generation, report recovery, AST source/file indexing and repository gates. |
| `.github/workflows/` | Multi-OS/core/browser/native acceptance plus three-language CodeQL. |
| `docs/` | Design decisions, risk model, operations, primary research, validation and exact source/file navigation. |

Every authored file has a specific responsibility in [FILE_CATALOG](docs/FILE_CATALOG.md).
Source headers link to [SOURCE_MAP](docs/SOURCE_MAP.md), generated from Python and
TypeScript ASTs and C++ syntax nodes. This keeps function/class/parameter/assigned-name
line references current rather than maintaining fragile hand-numbered comments.

## Limits that matter

The tested application is **one reference MAVSDK client and one owned SIH quadrotor**,
not every autopilot/application/transport. ArduPilot, hardware-in-loop, real radios,
public hosting, mobile installers, flight certification and general DUT plugins are
not implemented. Extending clients/versions requires reviewed source and independent
new acceptance—not a configuration change that silently assumes compatibility.

MAVLink framing metadata is not CRC/signature verification; signing is not encryption.
The relay intentionally breaks timing/order/delivery inside a lab. Its packet IDs are
not MAVLink sequence numbers or loss-rate estimates. Cached health/armed/mode are
latest reported state, not independently measured truth. A trusted OS could proxy
loopback or replace source/binaries; source/build hashes do not attest against that
attacker. An unconfirmed upload may already have changed the autopilot's mission.

The viewer shows retained samples and trace excerpts, not continuous data, navigation,
trajectory prediction or proof of anonymity. Failed/partial records and unsupported
capabilities must remain visible. Never connect this lab to operational aircraft.

Contact: [Jason Stys on LinkedIn](https://www.linkedin.com/in/jason-stys-31b30b351/).
Use public issues only for non-sensitive reproducible questions. See [SECURITY](SECURITY.md).
