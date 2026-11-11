# Installed Windows 0.2.0 validation

By Jason Stys. 11 November 2026.

These observations describe the independently downloaded, published **0.2.0** application built from `cd733ce544242a073cab60a3477df18d02558ed1`. Earlier Office editions, failed-run evidence and releases remain unchanged.

## Purpose and practical improvements

Inspect imported offline MAVLink evidence, packet-local timing/drop/correlation results and ambiguous boundary states through the complete bundled viewer. No aircraft or live control connection is opened.

Review relay-local delay, drop, unobserved and ambiguous packet correlation with exact evidence boundaries. Helps diagnose simulated transport faults without claiming receiver acknowledgement or loss from incomplete observations.

## Observed validation

**Real native workflows: Passed.** The unchanged full installed-app consumer passed actual file import, original engine/results, role boundaries where applicable, exports, negative cases and normal owner Quit.

**Source and security: Passed.** All required main workflows for the runtime revision passed; processed CodeQL analyses reported zero open main alerts before release.

**Distribution identity: Verified.** All 2 assets matched provider/checksum identities; all 72 installed files remained unchanged during acceptance.

**PC scope: Verified.** New per-user version folder and individual links verified. Synthetic inputs and isolated outputs only; existing data and Docker were not used or changed.

## Illustrated use and implementation

The [four-page guide](windows-application-guide-0.2.0.docx) contains two actual installed-app screenshots, a worked user journey, an immutable source-code excerpt and operating limits. The [review manifest](windows-application-guide-0.2.0.json) binds exact Word, image, source and individually inspected page identities. Prepared cases are inputs inside the actual application, never separate demonstration apps.

## Installation and limits

Keep the complete extracted ZIP together and launch MavlinkEvidenceStudio.exe. No system runtime or terminal setup is needed.

Open the verified Desktop icon. Save the reviewed report JSON and derived packet-review export explicitly. Reopening starts an empty/example viewer; reimport your saved report to continue. The derived packet review is a separate export.

Offline evidence viewer on the PC; actual compatibility/SITL execution requires the separately documented Linux environment. No live-aircraft endpoint.

Tests used synthetic offline inputs and isolated outputs. No aircraft, emergency dispatch or production data was accessed. This viewer keeps its active review in memory; save files explicitly before quitting.

Individual shortcut targets were read-back verified. Actual installed-executable acceptance is separate from ordinary default-profile shortcut activation, which was not independently exercised. Only synthetic inputs and isolated outputs were used; normal user data and Docker were not opened or changed. This documentation commit requires its own original hosted checks and processed security analyses; prior runtime evidence does not certify later source changes.
