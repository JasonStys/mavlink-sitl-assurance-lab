# Contributing

By Jason Stys. Original implementation is AI-assisted; successful automated checks
are not an independent human code/security audit.

Start with the README and reproduce the exact locked toolchain. Keep changes small,
use descriptive names and document units/unknown state. Source headers link to the
generated declaration map; classes/functions describe their responsibility. Regenerate
`tools/schema.py` and `tools/docs_index.py` outputs after relevant changes and check
them rather than manually changing line numbers or generated fixtures.

Preserve failed evidence. Never raise size/time/coverage limits solely to hide a
regression, treat unsupported/unreached tests as passes, substitute a mock native
client, or bypass actual observations with SDK acknowledgement status. Do not add
real-aircraft endpoints, downloaded executable plugins or arbitrary command input.

Run all local gates and actual native jobs for changed native behavior. Review source
for bounds, lifetime, concurrency, unit conversions, untrusted content and honest
classification. Synthetic browser/unit fixtures are not native integration evidence.
Dependency upgrades require fresh lock hashes, audit and matrix acceptance. A new
autopilot is unsupported until its separate actual build/scenarios pass.

Paid/cloud/hardware deployment and Actions cleanup/retention changes need explicit
owner approval. Do not alter other host services to make this lab pass. Portfolio
contact: [Jason Stys](https://www.linkedin.com/in/jason-stys-31b30b351/).
