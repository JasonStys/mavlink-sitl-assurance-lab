# Documentation refresh — 2026-11-09

By Jason Stys.

This documentation-only edition describes source `9705148c159ca546a85c2f9bc174a881b6556bc3`. It does not change application behavior, accounts, private data, installers or published releases.

## Published editions and completed review

| File                                     | Bytes | SHA-256                                                            | Reviewed scope                    |
| ---------------------------------------- | ----: | ------------------------------------------------------------------ | --------------------------------- |
| [project-guide.docx](project-guide.docx) | 47213 | `ae751f52206826baa797edf1c4be7bf1353caa45d2c134ec9a53b2491fe21533` | 7 pages, each viewed individually |

Word review checked plain black titles, readable pagination, whole table rows, source references, practical limits and absence of clipping or overflow. Render receipts were matched to the current DOCX digest before approval. Workbook review inspected both tab previews and actual exported Table/autoFilter elements; recalculated success/failure summaries were compared independently with workflow metadata. Static previews do not draw Excel dropdown arrows; the exported workbook contains the actual filters.

## Evidence and change boundary

- Functional baseline: `9705148c159ca546a85c2f9bc174a881b6556bc3`.
- Workflow observation: `2026-11-10T05:25:40.628667+00:00`; exact run URLs and source identities remain in [publications.json](publications.json).
- Local document-package validation verifies exact copied bytes, Office ZIP integrity, approved page/tab identities and internal documentation links. Repository-specific documentation and source-policy commands are run separately and recorded in the integration handoff.
- Source/index metadata is regenerated using the repository’s existing tools. Existing privacy, security, coverage and workflow gates are retained.
- PR and later main workflows must pass independently. This record does not claim future or unrun integration CI success.

## Interpretation

The Word files document the cited source; dated source reports retain their original execution scope. A passing workflow is distinct from completed analysis with zero findings, and neither establishes production suitability. The Excel source inventory is not a per-test execution report. Checksums identify exact bytes, not a signature or publisher attestation.

Use the [handbook](../handbook.md) to choose usage, design, security and test documentation. Keep editable Markdown and reviewed editions together; do not replace historical measurements with undated claims.

## Integration-local validation

All seven final Word pages were individually reviewed against the current DOCX
render digest. Copied Word bytes, ZIP integrity, publication/source/workflow
identities and handbook/report links passed independent checks. The existing
repository privacy scan now reads XML and relationships from only the three
exact named documentation editions through a bounded, single-descriptor Office
reader; it continues scanning all source text and rejects unknown binary files.
Eight actual ZIP regressions passed. The complete Python suite passed 87 tests
with the unchanged 144/145 measured core lines (99.31%) and 90% requirement.
Ruff, source/catalog regeneration and checks, production bundle budgets and
`git diff --check` passed.

These documentation checks do not rerun Linux-only PX4/MAVSDK integration or
sanitizers; their original hosted gates remain required. No flight runtime,
private records, installed software or public release bytes are changed.
