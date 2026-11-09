"""Jason Stys: independent packet ledgers and create-only CLI evidence. Map: docs/SOURCE_MAP.md."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from assurance.delivery import delivery_review
from assurance.report import Report, synthetic_report


def event(identifier=1, **changes):
    """Build fictional metadata, not captured aircraft traffic."""
    return (
        dict(
            event="receive",
            phase="delay",
            at_ms=100,
            packet_id=identifier,
            direction="to_sdk",
            size=12,
            reason="delay",
            framing_complete=True,
            ids=[0],
        )
        | changes
    )


def report(events, seen=None):
    """Keep the existing strict contract and original case outcomes intact."""
    return Report.model_validate(
        synthetic_report().model_dump()
        | {
            "trace": events,
            "trace_events_seen": len(events) if seen is None else seen,
        }
    )


@pytest.mark.parametrize(
    ("events", "status", "delays"),
    [
        (
            [event(), event(event="send", at_ms=160), event(event="send", at_ms=140)],
            "relay-send-observed",
            [40, 60],
        ),
        ([event(reason="drop")], "intentional-drop", []),
        ([event(reason="drop_ack")], "intentional-drop", []),
        ([event()], "send-not-observed", []),
        ([event(event="send")], "receive-not-retained", []),
        ([event(), event()], "ambiguous-receive", []),
        ([event(), event(event="send", at_ms=99)], "inconsistent-metadata", []),
        ([event(), event(event="send", direction="to_px4")], "inconsistent-metadata", []),
        ([event(), event(event="send", size=11)], "inconsistent-metadata", []),
        ([event(reason="drop"), event(event="send")], "inconsistent-metadata", []),
    ],
)
def test_hand_accounted_correlations(events, status, delays):
    """Expected statuses are manually specified independently of the grouping algorithm."""
    source = report(events)
    before = source.model_dump_json()
    review = delivery_review(source)
    assert review["packets"][0]["status"] == status
    assert review["packets"][0]["local_delays_ms"] == delays
    assert review["status_counts"] == {status: 1}
    assert review["reported_outcome"] == "passed"
    assert source.model_dump_json() == before


def test_retention_and_phase_boundaries_are_not_loss_or_mavlink_sequence():
    """Relay IDs correlate across exercise phases; no fabricated source-clock delay."""
    source = report([event(9), event(9, event="send", phase="blackout", at_ms=120), event(2)], 100)
    review = delivery_review(source)
    assert review["truncated"]
    assert [row["packet_id"] for row in review["packets"]] == [2, 9]
    assert review["packets"][1]["phases"] == ["blackout", "delay"]
    assert review["packets"][1]["local_delays_ms"] == [20]
    assert review["packets"][0]["extra_send_count"] == 0
    assert delivery_review(report([]))["packets"] == []


def test_cli_creates_review_and_refuses_existing_output(tmp_path):
    """Exercise real strict input loading and protect the original source and prior export."""
    source, output = tmp_path / "input.json", tmp_path / "review.json"
    source.write_text(report([event(reason="drop")]).model_dump_json(), encoding="utf-8")
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "tools/delivery_review.py"),
        "--input",
        str(source),
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, check=False)  # noqa: S603 - fixed test helper
    assert completed.returncode == 0, completed.stderr
    saved = output.read_bytes()
    assert json.loads(saved)["packets"][0]["status"] == "intentional-drop"
    assert subprocess.run(command, capture_output=True, check=False).returncode != 0  # noqa: S603
    assert output.read_bytes() == saved
