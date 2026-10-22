# Validation record — 0.1.0

By Jason Stys. Observations are not release certification or an independent human audit.

Initial local Windows checks passed the Release C++ policy kernel, including 20,000
seeded malformed inputs, 50,000 measured forwarding iterations and queue bounds.
The observed MSVC Release timing was 9,283 microseconds for that synthetic iteration
loop, not a real-network throughput claim or a portable performance promise.

The first Python contract/extraction suite passed 33 cases at 99.02% statement coverage
of the report contract. The TypeScript suite passed 35 cases at 96.77% statements,
96.03% branches and 100% functions for the pure validation/filter/graph module.
These are not whole-application or native SDK coverage percentages. The production
viewer build and exact formatting passed. Native integration must be proven separately
by both actual upstream builds and eight required scenarios on each version.

Setup history: the restricted Windows process could not read the Visual Studio SDK
registry; normal scoped process permissions used the existing installation without
changing the host. A signed/unsigned C++ comparison was corrected, not suppressed.
Node's JSON module import attribute was added to browser tests after the first browser
setup failed. No failed setup attempt counts as acceptance. Thresholds were not lowered.

Storage checked before Actions: 62,959,952 current artifact bytes and 8,185,324,614
separate cache bytes across 96 owned repos. Billing quota/percentage was unavailable.
Nothing was archived/deleted and no retention/billing settings were changed. New
workflows upload neither caches nor artifacts; full bounded report JSON remains in
Actions job logs. No paid resource, real aircraft, external AI provider, private user
account or host Docker repair was used.

Source-linked final native results, browser totals and completed Actions observations
will be recorded only after those gates actually pass. Missing/failed native work
must not be replaced by a synthetic fixture or described as operational assurance.

The first native attempt built PX4 1.17.0 and passed all eight actual scenarios in
[run39705100848](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions/runs/39705100848),
source `b9706d10e0b80d50d56ba8b8a68839bab0f05594`. Observations included 250ms minimum
delay, 536 packet-order inversions, 829 duplicated packet IDs, 6.45s stale link,
two stored mission items despite unconfirmed upload, takeoff at3.208m, 19% actual
simulated battery, and two owned boots without replay. These are native SIH observations,
not real flight or proof of every application/autopilot. CodeQL's three language jobs,
all four core OS/Python jobs and the original nine browser journeys passed.

PX4 1.16.1 failed **before runtime acceptance** because its upstream version-header
generator indexed missing NuttX tags in a shallow recursive checkout. This was a
workflow metadata-preparation defect, not observed application/autopilot misbehavior.
The workflow now fetches official version tags and rechecks the unchanged pinned HEAD;
upstream source and acceptance assertions were not patched or weakened. Review also
added tested planned-stop/crash classification, calendar/UUID checks, per-phase packet
excerpts and trace filtering. Final versions still require their own actual acceptance.
