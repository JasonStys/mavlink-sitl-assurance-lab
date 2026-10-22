"""Jason Stys: independent evidence/outcome/boundary oracles; not native simulator results.

Test/function/variable lines: docs/SOURCE_MAP.md. These tests never open a socket,
execute a third-party report or treat synthetic fields as real PX4 measurements.
"""

import json

import pytest
from pydantic import ValidationError

from assurance.report import (
    MAX_REPORT_BYTES,
    PINS,
    Report,
    dispatch_allowed,
    load_report,
    outcome,
    save_report,
    synthetic_report,
)


def payload():
    """Return an independent mutable envelope of clearly synthetic teaching evidence."""
    return synthetic_report().model_dump()


def test_synthetic_round_trip_and_no_overwrite(tmp_path):
    """Exclusive output preserves previous evidence; round-trip keeps the synthetic label."""
    report = synthetic_report()
    target = tmp_path / "new" / "report.json"
    save_report(target, report)
    assert load_report(target) == report
    assert report.mode == "synthetic" and report.binary_sha256 is None
    with pytest.raises(FileExistsError):
        save_report(target, report)


@pytest.mark.parametrize(
    "age,battery,connected,allowed",
    [
        (0, 25, True, True),
        (2, 100, True, True),
        (2.001, 100, True, False),
        (-0.01, 50, True, False),
        (1, 24.99, True, False),
        (1, 101, True, False),
        (1, 50, False, False),
        (float("nan"), 50, True, False),
        (1, float("inf"), True, False),
    ],
)
def test_dispatch_independent_oracle(age, battery, connected, allowed):
    """Closed safety boundaries do not depend on UI state or a cached green summary."""
    assert dispatch_allowed(age, battery, connected) is allowed


@pytest.mark.parametrize(
    "status,expected", [("failed", "failed"), ("unsupported", "partial"), ("passed", "passed")]
)
def test_recomputed_outcome(status, expected):
    """One failed or unsupported scenario cannot be concealed by other passing cases."""
    data = payload()
    data["checks"][0]["status"] = status
    data["outcome"] = expected
    report = Report.model_validate(data)
    assert outcome(report.checks) == expected
    if status != "passed":
        data["outcome"] = "passed"
        with pytest.raises(ValidationError, match="Summary"):
            Report.model_validate(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(extra="hidden"),
        lambda row: row.update(source_commit="0" * 40),
        lambda row: row.update(checks=row["checks"][:-1]),
        lambda row: row["checks"][0].update(name=row["checks"][1]["name"]),
        lambda row: row.update(mode="native"),
        lambda row: row.update(counters={"received": -1}),
        lambda row: row.update(notes=["x" * 601]),
        lambda row: row["checks"][0].update(metrics={"invalid": float("inf")}),
        lambda row: row["observations"][0].update(battery_pct=101),
        lambda row: row.update(schema_version=2),
    ],
)
def test_invalid_envelopes_rejected(mutate):
    """Invalid version/identity, fabricated green, nonfinite and excessive data fail closed."""
    data = payload()
    mutate(data)
    with pytest.raises(ValidationError):
        Report.model_validate(data)


def test_trace_contract_and_native_hash():
    """Framing metadata cannot claim arbitrary message IDs or impossible retained counts."""
    data = payload()
    data.update(mode="native", binary_sha256="a" * 64)
    trace = {
        "event": "receive",
        "at_ms": 10,
        "packet_id": 1,
        "direction": "to_sdk",
        "size": 12,
        "reason": "delay",
        "framing_complete": True,
        "ids": [0],
    }
    data.update(trace=[trace], trace_events_seen=1)
    assert Report.model_validate(data).source_commit == PINS["1.17.0"]
    data["trace"][0]["ids"] = [0x1000000]
    with pytest.raises(ValidationError, match="24-bit"):
        Report.model_validate(data)
    data["trace"][0]["ids"] = [0]
    data["trace_events_seen"] = 0
    with pytest.raises(ValidationError, match="retained"):
        Report.model_validate(data)


def test_load_bounds_duplicate_keys_and_invalid_json(tmp_path):
    """Untrusted file input is size bounded and duplicate-key envelopes cannot be ambiguous."""
    target = tmp_path / "input.json"
    target.write_bytes(b" " * (MAX_REPORT_BYTES + 1))
    with pytest.raises(ValueError, match="two MiB"):
        load_report(target)
    target.write_text('{"mode":"native","mode":"synthetic"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_report(target)
    target.write_text('{"broken":', encoding="utf-8")
    with pytest.raises(ValueError):
        load_report(target)


def test_write_budget_is_not_silently_truncated(tmp_path):
    """Even structurally valid reports must satisfy their serialized byte budget."""
    data = payload()
    data.update(
        trace=[
            {
                "event": "receive",
                "at_ms": 10,
                "packet_id": index + 1,
                "direction": "to_sdk",
                "size": 2048,
                "reason": "forward",
                "framing_complete": True,
                "ids": [0xFFFFFF] * 256,
            }
            for index in range(2500)
        ],
        trace_events_seen=2500,
    )
    report = Report.model_validate(data)
    with pytest.raises(ValueError, match="two MiB"):
        save_report(tmp_path / "large.json", report)
    assert not (tmp_path / "large.json").exists()


def test_schema_exports_all_required_scenarios():
    """The browser consumes generated structural constraints, not executable report content."""
    schema = Report.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["trace"]["maxItems"] == 2500
    assert json.loads(json.dumps(schema))["$defs"]["Trace"]["properties"]["ids"]["maxItems"] == 256
