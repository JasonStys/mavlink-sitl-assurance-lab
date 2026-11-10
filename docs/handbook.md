# MAVLink SITL Assurance Lab handbook

By Jason Stys.

Review relay-local delay, drop, unobserved and ambiguous packet correlation with exact evidence boundaries.

Helps diagnose simulated transport faults without claiming receiver acknowledgement or loss from incomplete observations.

## Read the documentation

| Edition                                          | Audience and contents                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| [project-guide.docx](reports/project-guide.docx) | User and developer guide: purpose, current usage, design, boundaries and source references. |

The editable Markdown remains the maintenance source. The Word files are readable editions, and the workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [OPERATIONS](OPERATIONS.md)

### Design and contracts

- [ARCHITECTURE](ARCHITECTURE.md)
- [RESEARCH](RESEARCH.md)

### Security and validation

- [SECURITY](SECURITY.md)
- [TESTING](TESTING.md)
- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`9705148c159ca546a85c2f9bc174a881b6556bc3`](https://github.com/JasonStys/mavlink-sitl-assurance-lab/tree/9705148c159ca546a85c2f9bc174a881b6556bc3). The observed functional workflow baseline is `9705148c159ca546a85c2f9bc174a881b6556bc3`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PRACTICAL_WORKFLOWS_20261109.md)
- [Current Actions](https://github.com/JasonStys/mavlink-sitl-assurance-lab/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- A relay send is not receiver acknowledgement or end-to-end delivery proof.
- Missing correlation metadata does not prove loss; imported retention and identity declarations remain self-reported.
- The ledger does not verify CRC, signature, payload authenticity or operational aircraft safety.
- Source-first project with current package/service validation; no public native desktop application release is supplied.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
