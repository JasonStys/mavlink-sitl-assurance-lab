# Office-package inspection guard — 2026-11-10

By Jason Stys. This is a repository documentation-input correction; application behavior and released assets are unchanged.

The exact named Office reader already bounded package/member expansion, rejected VBA, and returned XML and relationship text to the existing repository checks. It did not reject an opaque member below `/embeddings/`. Such a member could be accepted without being treated as inspectable text. The reader never executes Office content, so this is not a claim of an application code-execution exploit.

The member admission condition now also refuses the literal `/embeddings/` path component, using the existing case-normalized name. Two real compressed-ZIP negative fixtures add inert `word/vbaProject.bin` and `word/embeddings/inert.bin` entries to an otherwise accepted named Word package. Both must raise the existing unsupported-member error. Positive XML/relationship, invalid/unknown-input and bounded-expansion checks remain enabled. No extension-wide binary exclusion or secret-scan bypass was introduced.

## Observed local validation

- Full existing Python suite: **90 passed**. The configured `assurance` runtime coverage scope measured **99.31%** with its existing coverage floor and exclusions unchanged. These runtime percentages do not claim coverage of all documentation helper code.
- Original Ruff checks and formatting passed across the runtime, tests and tools. Existing strict mypy passed where configured.
- Frontend unit suite: **47 passed**; the strict production build passed.
- Existing repository/header/privacy and generated-index checks passed after regenerating the original indexes.
- The approved Word/Excel bytes were independently SHA-256 compared before and after the repair and remain identical. No Office package was rebuilt.

No test warning was reported.

The checks ran on Windows with the repository's isolated environment and locked installed tools. Original cross-platform, browser, native/sanitizer, release and any simulator/service CI jobs remain required on the pull request; this report does not claim they were rerun locally. No physical drone/device, external collector, live enforcement, Docker repair, installed application or released package was accessed or changed. This bounded source-policy fix does not make Office uploads safe in a public service or certify the contents of arbitrary documents.
