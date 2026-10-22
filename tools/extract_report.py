"""Jason Stys: recover a bounded report from locally downloaded GitHub job logs.

Functions/variables/lines: docs/SOURCE_MAP.md. Reads text only, strips timestamp
prefixes, validates the envelope and creates a new file. Never executes archived data.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assurance.report import MAX_REPORT_BYTES, Report, parse_report, save_report  # noqa: E402


def extract(text: str) -> Report:
    """Require one complete marker-delimited JSON envelope; accept plain or Actions timestamped lines."""
    collecting = False
    complete = False
    parts = []
    size = 0
    for raw in text.splitlines():
        line = raw.split(" ", 1)[1] if raw[:4].isdigit() and " " in raw else raw
        if line == "REPORT_BEGIN":
            if collecting or complete:
                raise ValueError("Multiple/overlapping report records")
            collecting = True
        elif line == "REPORT_END" and collecting:
            collecting, complete = False, True
        elif collecting:
            size += len(line.encode("utf-8")) + 1
            if size > MAX_REPORT_BYTES:
                raise ValueError("Embedded report exceeds two MiB")
            parts.append(line)
    if not complete or collecting:
        raise ValueError("No complete report; log may be truncated")
    return parse_report("\n".join(parts))


def main():
    """Extract from one locally downloaded job log, preserving any existing output evidence."""
    parser = argparse.ArgumentParser(description="Read downloaded log text; never execute it")
    parser.add_argument("log", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.log.open("rb") as source:
        content = source.read(16 * 1024 * 1024 + 1)
    if len(content) > 16 * 1024 * 1024:
        raise ValueError("Log exceeds sixteen MiB input budget")
    report = extract(content.decode("utf-8"))
    save_report(args.output, report)
    print(
        f"Recovered {report.mode} / {report.version} / {report.outcome}; verify source-linked provenance separately"
    )


if __name__ == "__main__":
    main()
