"""Jason Stys: deterministic serialization schema and synthetic fixture generation/checking.

Functions/variables/lines: docs/SOURCE_MAP.md. Only the reviewed schema vocabulary is
allowed by the CSP-safe browser interpreter. It is not a general JSON Schema engine.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assurance.report import Report, synthetic_report  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = {
    "$defs",
    "$ref",
    "type",
    "anyOf",
    "const",
    "enum",
    "required",
    "properties",
    "additionalProperties",
    "minLength",
    "maxLength",
    "pattern",
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
    "maxProperties",
    "items",
    "default",
    "description",
    "title",
}


def vocabulary(rule):
    """Fail generation/checking on an unsupported schema keyword instead of silently weakening validation."""
    if not isinstance(rule, dict):
        return
    unknown = set(rule) - KEYWORDS
    if unknown:
        raise ValueError(f"Implement new schema keywords in the viewer: {sorted(unknown)}")
    for key in ("$defs", "properties"):
        for child in rule.get(key, {}).values():
            vocabulary(child)
    for child in rule.get("anyOf", []):
        vocabulary(child)
    for key in ("items", "additionalProperties"):
        vocabulary(rule.get(key))


def main():
    """Generate canonical schema/demo files, or verify exact deterministic content in CI."""
    schema = Report.model_json_schema(mode="serialization")
    vocabulary(schema)
    demo = synthetic_report().model_dump()
    demo.update(
        run_id="00000000-0000-4000-8000-000000000042", created_utc="2026-10-22T00:00:00+00:00"
    )
    for name, data in (("ui/schema/report.schema.json", schema), ("examples/synthetic.json", demo)):
        content = json.dumps(data, indent=2) + "\n"
        target = ROOT / name
        if "--check" in sys.argv:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale {name}; run python tools/schema.py")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    print("Canonical schema and clearly synthetic example verified")


if __name__ == "__main__":
    main()
