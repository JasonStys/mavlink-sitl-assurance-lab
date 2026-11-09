"""Jason Stys: create-only offline packet review export. Symbols: docs/SOURCE_MAP.md."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assurance.delivery import delivery_review  # noqa: E402
from assurance.report import load_report  # noqa: E402


def main():
    """Read one strict size-bounded report and refuse to overwrite any existing output."""
    parser = argparse.ArgumentParser(description="Review retained local relay packet metadata")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = delivery_review(load_report(args.input))
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(review, indent=2) + "\n")


if __name__ == "__main__":
    main()
