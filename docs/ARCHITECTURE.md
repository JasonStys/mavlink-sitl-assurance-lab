# Architecture and accepted decisions

Author: Jason Stys. Status: accepted for the simulator-only prototype, 2026-10-21/22.
AI-assisted implementation; not independent human approval or operational authority.

## Requirements and data flow

```text
Python independent scenario oracles
    ├── own pinned PX4 SIH child + source/executable identity
    ├── native MAVSDK reference client :14541
    │             ↕ opaque datagrams
    └── C++ bounded relay :14540 ↔ owned PX4 MAVLink :14580
                   │ metadata + cumulative counters
                   ▼
     versioned report / expected vs observed / failed or partial outcomes
                   ▼
     local-only TypeScript viewer → reviewed JSON download
```

R1 compatibility: exact two-version source matrix, native SDK pin and actual builds.
R2 reproducible faults: pure bounded C++ policy and explicit duration acknowledgements.
R3 independent evidence: relay-ID receive/send correlation plus actual SDK observations.
R4 honest failure: required scenarios, summary consistency, failed/unreached classification.
R5 safe local review: strict bounded JSON, duplicate-key rejection, text-only DOM, CSP.
R6 maintainability: locked tools, readable comments, AST indexes and multi-language CI.

## ADR-001 — C++ policy, Python oracles, TypeScript evidence

Context: exercise actual autopilot interfaces without building another flight controller.
Decision: C++20 for deterministic byte/queue policy and a Linux UDP relay, Python for
native SDK orchestration/report contracts, TypeScript for portable browser review.

Considered a Python-only relay (fewer tools, less native integration evidence) and a
monolithic C++ UI/controller (more interface/lifetime complexity, slower iteration).
The chosen split has modest language-boundary cost but makes policy independently
testable without sockets and expected behavior independent of the relay's counters.
The viewer never controls the simulator. Revisit an adapter API only after independent
clients need it; this version does not dynamically execute user-supplied DUT plugins.

## ADR-002 — fixed loopback ownership rather than arbitrary endpoint configuration

Context: fault injection is appropriate in authorized simulations, not real air links.
Decision: Linux-only fixed source/build paths, exact upstream identity, unused-port
precheck, owned Popen children, fixed loopback peers, bounded stdin vocabulary and
60-second fault durations. Reject existing ports rather than attaching to a service.

Alternatives include remote UDP/serial inputs and a general network-proxy product;
both expand the threat/operational authority beyond this lab. A malicious local OS
can still race/proxy ports or alter tools. The checks prevent accidental attachment
on a trusted isolated host, not attestation against that attacker. No paid service,
Docker repair, new firewall rule, administrator account or aircraft hardware is used.

## ADR-003 — bounded report contracts, local-only review, no evaluated schemas

Decision: Pydantic's generated canonical serialization schema is checked into source.
The viewer interprets only its explicitly reviewed small vocabulary without eval or
runtime code generation. Schema generation fails on unknown keywords. JSON syntax
uses the locked jsonc-parser with comments/trailing commas prohibited and duplicate,
depth and node-budget checks. The schema is never supplied by an uploaded report.

A general schema engine adds capabilities not needed here; runtime code-generation
validators complicate a strict CSP. The small interpreter requires maintenance and
shared contract tests and is **not** a complete JSON Schema implementation. Browser
and backend also independently check derived outcomes, source pins and custom bounds.
Imported report provenance remains self-reported; this is not digital signing.

Full JSON travels in Actions job logs with explicit markers, not storage-consuming
artifacts/caches. Local generated reports are ignored and never overwritten. Reporting
all source-linked CI evidence is more verbose in logs but avoids erasing failed runs.
Revisit signed provenance and a private evidence store before team/production use.

## Bounds, complexity and scale

For datagram B<=2048, pending Q<=256 and retained trace E<=2500: framing O(B),
policy receive O(B+Q) for pair lookup, queue drain O(Q), no unbounded packet backlog.
Queued opaque bytes are at most 524,288 plus bounded container overhead. Relay traces
are drained continuously; the parent retains only E records but cumulative counters
and seen counts expose truncation. A relay watchdog is fifteen minutes.

Report input <=2 MiB; downloaded log input <=16 MiB; observations<=200; eight required
cases; notes<=12; metrics/counters<=20. JSON/schema work is linear in bounded syntax
size; nested syntax is limited to depth32 and 50,000 nodes. Only the last 100 retained
packet events render in the UI. Telemetry graph shows sample order, not uniform time.

These are prototype/resource bounds, not a traffic-throughput SLA. Benchmarks report
actual wall-clock observations without host-independent latency promises. SIH dynamics,
SDK queues and OS scheduling are external. One client/aircraft/process workspace is
supported; no multi-tenant service, cloud scaling or real-time guarantee is claimed.
