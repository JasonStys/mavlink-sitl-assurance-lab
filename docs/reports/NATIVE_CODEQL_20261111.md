<!-- Jason Stys: dated current-main CodeQL quality corrections and retained validation boundaries. -->

# Native CodeQL quality follow-up — 2026-11-11



These changes respond to actual full-main CodeQL quality notes before the first0.2.0 desktop release. They do not suppress, dismiss or exclude queries. No already-published release or installed user profile is altered.



## Corrections



- Console Ctrl+C now explicitly acknowledges closing the local evidence viewer. The existing managed server context still performs cleanup before the normal stopped message.

- Both actual launcher control-flow variants assert the acknowledgement and context closure. The full existing HTTP/authority/Quit and report suites remain active. This introduces no simulator execution on Windows.



## Local observation



| Gate | Observed result |

| --- | --- |

| Full original Python package suite | 154 passed; 99.27% coverage against unchanged90% floor |

| Original TypeScript test denominator | 53 tests;97.70% statements,96.66% branches,100% functions,99.13% lines |

| Original strict UI build, formatting and Ruff | Passed |

| Generated source/file navigation and original public-source hygiene | Passed after regeneration |



No policy, role, database schema, UI workflow or secret-bearing data path is changed. Native build/3OS acceptance, original browser checks and a new full-main CodeQL analysis must pass on the eventual exact merged source before release. Earlier accepted package measurements remain bound to their earlier commits; they are not rebound to this correction. The original educational/offline boundaries, unsigned-portable limits and manual desktop-opener limitations remain.


## Hosted Windows request-order regression

The first follow-up run passed both genuine PX4 integrations, all other core platforms and all three native desktop jobs, but Windows encountered WinError10053 in a negative Quit test. The HTTP client raced a second unauthorized body write with the server's intentional early refusal and connection close. Header-only rejection fixtures now declare their actual fixed body length but send no body, proving the existing header/authentication checks respond before waiting on that data. The real different-action and authorized Quit cases still send their complete bodies. A new valid-token/headers-only case proves the existing two-second body deadline returns400 and leaves the application running. No status, credential, read deadline or retry was weakened. The failed hosted run remains historical evidence.
