# Operations and evidence review

By Jason Stys. Use an isolated authorized lab, not an operational aircraft computer.

## Viewer

Follow the README Node24 quick start. Preview binds loopback port8851; do not proxy
it to the internet. Choose the synthetic example to learn the controls, then import
a native `.json` report. Inspect the summary, every expected/observed result, outcome
filter, observation table, retained trace, source/executable hashes and limitations.
Filters never change the overall outcome. Download creates an explicit local copy.

The local file picker uploads nothing. Reports can still contain private operational
metadata supplied by their author: keep those files on private storage, close the tab
after use and do not post private evidence publicly. No passwords or user accounts
are collected. An imported native claim is not authenticated simply by passing schema.

## Actual native run on Linux

Use a fresh repository checkout/runtime for each run; do not delete/overwrite an older
workspace to reuse its evidence name. Install Python3.12 and the CI-listed Linux build
dependencies: build-essential, CMake, ninja-build, bc and libeigen3-dev. Leave existing
Docker/host services untouched. GitHub-hosted jobs provide clean separate runners.

1. Clone official `https://github.com/PX4/PX4-Autopilot.git` into `.runtime/px4`.
2. Check out **one exact commit from README**, then initialize that commit's recursive
   submodules. Do not use an unpinned branch, arbitrary binary or different simulator.
3. In this repo's virtual environment, install `requirements-native.lock` with
   `python -m pip install --require-hashes -r requirements-native.lock`.
4. Build the lab relay with `cmake -S . -B .runtime/build -DCMAKE_BUILD_TYPE=Release`
   and `cmake --build .runtime/build --parallel 2`.
5. Build actual PX4 using `make -C .runtime/px4 px4_sitl_default -j2`. This is the real
   build target used by the reviewed release sources, not an assumed latest-main target.
6. Run `python -m assurance.runner --version 1.17.0` (or1.16.1 for its exact source).
   All three ports14540/14541/14580 must be unused. Never redirect/bridge these ports.
7. Read the exit code and resulting `.runtime/report-VERSION.json`. Nonzero or
   failed/partial means the full assurance suite did **not** pass. Open that report
   in the viewer even on failure; unsupported/not-reached cases remain explicit.

The runner launches one SIH quadrotor with PX4's public training defaults and owns
the reference SDK and relay. Faults are applied while grounded before the nominal
mission. Low-battery testing changes only actual simulator battery parameters,
arms on the ground and then disarms; it does not inject a fake observation.
The final restart happens grounded, expires the old connection and creates a new SDK
session. The suite does not promise safe handling of arbitrary airborne restarts.

## Evidence from Actions without artifact storage

Open a specific **Genuine PX4 VERSION** job, download its plain text log, then run
`python tools/extract_report.py downloaded-job.log .runtime/recovered-report.json`.
Use one job's log, not a concatenation of both matrix jobs. One complete REPORT_BEGIN /
REPORT_END envelope is required. Truncated, multiple, oversized, duplicate-key or
schema-invalid data fails; no archived content is executed. Existing output is preserved.

The compact NATIVE_ACCEPTANCE record summarizes assertions, source/build identity,
counters and outcomes. Full report JSON includes bounded telemetry and trace metadata.
Trace truncation is explicit. Python observation elapsed time and C++ relay elapsed
time have separate monotonic origins; do not treat them as precision synchronized clocks.

## Triage and recovery

- **Infrastructure:** dependency, source/build mismatch, occupied fixed port, dead relay,
  SDK/import/driver failure or cleanup failure. Inspect exact job setup/compile output;
  do not blame the tested client or label a missing tool as an application defect.
- **Simulator:** an owned PX4 process exits. Inspect `.runtime/px4-boot-N.log` and the
  compiled source/version; preserve failed evidence before rebuilding elsewhere.
- **Assertion:** observations did not meet expected behavior while the owned processes
  ran. Inspect arrival age, connected/armed/mode fields, actual packet events and counters.
- **Capability/not reached:** no evidence was obtained. It is not a passing scenario;
  adding a new client/autopilot requires its own implemented and tested integration.

An interrupted upload can already have stored mission items. Do not infer no effect
from a missing acknowledgement. The reference scenario waits for a resolved failure,
inspects the stored mission and only then performs a separate explicit upload. An
unresolved native-call deadline fails the run rather than allowing a blind retry.

## Shutdown, rollback and release gate

The runner closes SDK collectors, destroys the SDK, and terminates only its own
simulator/relay children; bounded termination escalates only for those exact owned
processes. Do not kill other applications, clear user caches or change host networking.
Keep old run folders private; remove them only with deliberate owner approval.

Before publishing: public-safe diff review, storage observation, all local/core/browser
and both actual native jobs, zero unresolved relevant CodeQL issues, lock audits,
current generated docs/schema and an exact final-commit check. No production/cloud
deployment is part of this source release; staging/on-call/production metrics are N/A.
Rollback triggers include false-green reports, payload leakage, unbounded queueing,
wrong-process attachment or failed cleanup. Stop only this lab, preserve evidence and
return to a reviewed earlier source in a new checkout. Never replay historical commands.
