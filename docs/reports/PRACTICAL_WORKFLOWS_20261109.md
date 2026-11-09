# Retained packet correlation workflow validation — 2026-11-09

Jason Stys: evidence-review functionality and observed local validation.

Purpose: help a simulator-software reviewer explain retained relay metadata,
without confusing a local relay send with reception or changing acceptance.
`assurance/delivery.py` and `ui/src/delivery.ts` independently derive the same
bounded grouping contract. `tools/delivery_review.py` loads the existing strict,
size-bounded report contract and refuses existing output paths. The source report
and reported outcome are never rewritten. Imported evidence remains self-reported.

## Observed checks

- Python: 79 passed; 99.31% measured core coverage; new delivery module 100%.
- TypeScript: 47 passed; statement 97.70%, line 99.13%, branch 96.66% coverage;
  new module included explicitly in the unchanged coverage gates.
- Production build and three-engine browser journeys: 15 passed, including real
  file import, truncated correlation, real JSON download, hostile-text/privacy,
  accessibility and narrow layouts. Alternate test port 18851 avoids user services.
- C++ rebuilt with MSVC: unchanged fault-policy CTest passed; 20,000 malformed
  cases, 50,000 measured packets, all existing oracle checks passed.
- Ruff, formatting, strict TypeScript, generated schema, source/file map and
  source/bundle hygiene checks are required by the existing workflow. Exact
  locked Python and npm advisory checks found no known vulnerabilities locally.

Manually specified oracle cases cover duplicate local sends and delay ordering,
both intentional drop reasons, unobserved send/receive, multiple receives,
direction/size/time inconsistencies, cross-phase IDs, truncation and empty input.
Tests assert source immutability and original outcome preservation. CLI tests run
the real executable entry point and verify overwrite refusal.

## Corrections and limits

Windows sandbox blocks asyncio loopback initialization: isolated local tests were
rerun with scoped permission. CMake was absent from PATH; the already installed
locked CMake executable and Visual Studio were used. Alternate-port browser tests
exposed a hardcoded test-origin assumption; the privacy assertion now checks the
configured exact origin, with its rejection rule intact.

This Windows validation does not rerun the Linux-only PX4 SIH native matrix or
sanitizers. Those existing mandatory CI gates remain unchanged and need source-
linked validation on publication. No GitHub Actions were triggered by this worker.
No hardware, operational traffic, real aircraft, payloads, interception or flight
commands were used. Delays are relay-local time differences, not source-clock or
end-to-end latency. Retention/completeness and identity are not cryptographic proof.
