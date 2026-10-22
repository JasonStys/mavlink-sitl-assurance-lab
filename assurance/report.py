"""Jason Stys: finite, bounded evidence contracts and honest outcome classification.

Classes/functions/parameters/variables and exact lines: docs/SOURCE_MAP.md. Schema
validation is not provenance attestation; imported files remain untrusted evidence.
"""

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

PINS = {
    "1.16.1": "94cb2012792b2ae89f0b147cfee53ee31ae550be",
    "1.17.0": "d6f12ad1c4f70ad3230afd7d86e971421e02fef4",
}
SCENARIOS = (
    "delay",
    "reorder",
    "duplicate",
    "blackout",
    "interrupted_upload",
    "nominal_mission",
    "low_battery",
    "autopilot_restart",
)
MAX_REPORT_BYTES = 2 * 1024 * 1024


class Contract(BaseModel):
    """Reject hidden fields and nonfinite numbers across every report component."""

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        strict=True,
        json_schema_serialization_defaults_required=True,
    )


class Check(Contract):
    """One independent expected/observed assertion group; unsupported never means passed."""

    name: str = Field(pattern=r"^[a-z_]{1,40}$")
    status: Literal["passed", "failed", "unsupported"]
    category: Literal["behavior", "assertion", "simulator", "infrastructure", "capability"]
    expected: str = Field(min_length=1, max_length=600)
    observed: str = Field(min_length=1, max_length=600)
    elapsed_ms: float = Field(ge=0, le=900000)
    metrics: dict[str, float] = Field(default_factory=dict, max_length=20)


class Observation(Contract):
    """Arrival-timed native state, not a source-clock timestamp or trajectory prediction."""

    at_ms: float = Field(ge=0, le=900000)
    phase: str = Field(pattern=r"^[a-z_]{1,40}$")
    altitude_m: float = Field(ge=-100, le=100)
    battery_pct: float = Field(ge=0, le=100)
    speed_m_s: float = Field(ge=0, le=100)
    mode: str = Field(pattern=r"^[A-Z_]{1,40}$")
    armed: bool
    age_s: float = Field(default=0, ge=0, le=900)
    connected: bool = True


class Trace(Contract):
    """Bounded packet metadata: no raw payload, identity/authentication or CRC-validity claim."""

    event: Literal["receive", "send"]
    phase: str = Field(default="unknown", pattern=r"^[a-z_]{1,40}$")
    at_ms: int = Field(ge=0, le=900000)
    packet_id: int = Field(ge=1)
    direction: Literal["to_sdk", "to_px4"]
    size: int = Field(ge=0, le=2049)
    reason: Literal["drop_ack", "drop", "reorder_pair", "duplicate", "delay", "forward", "delivery"]
    framing_complete: bool
    ids: list[int] = Field(max_length=256)

    @model_validator(mode="after")
    def valid_ids(self):
        """Bound message identifiers to MAVLink's 24-bit header range."""
        if any(not 0 <= value <= 0xFFFFFF for value in self.ids):
            raise ValueError("Message ID outside 24-bit range")
        return self


class Report(Contract):
    """Versioned report envelope with recomputed outcome and explicit tested/not-tested capabilities."""

    schema_version: Literal[1] = 1
    run_id: str = Field(
        pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
    )
    created_utc: str = Field(
        min_length=20,
        max_length=40,
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?\+00:00$",
    )
    author: Literal["Jason Stys"] = "Jason Stys"
    mode: Literal["native", "synthetic"]
    outcome: Literal["passed", "failed", "partial"]
    autopilot: Literal["PX4"] = "PX4"
    version: Literal["1.16.1", "1.17.0"]
    source_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    binary_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    mavsdk: Literal["4.0.6"] = "4.0.6"
    ardupilot: Literal["not_implemented"] = "not_implemented"
    checks: list[Check] = Field(min_length=1, max_length=16)
    observations: list[Observation] = Field(default_factory=list, max_length=200)
    trace: list[Trace] = Field(default_factory=list, max_length=2500)
    trace_events_seen: int = Field(ge=0)
    counters: dict[str, int] = Field(default_factory=dict, max_length=20)
    notes: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def consistent(self):
        """Reject false green summaries, duplicate/missing scenarios and mismatched upstream identities."""
        datetime.fromisoformat(
            self.created_utc
        )  # Reject impossible calendar dates, not merely malformed text.
        if self.source_commit != PINS[self.version]:
            raise ValueError("Version/source identity mismatch")
        names = [check.name for check in self.checks]
        if len(names) != len(set(names)) or set(names) != set(SCENARIOS):
            raise ValueError("Every named scenario must appear exactly once")
        if self.outcome != outcome(self.checks):
            raise ValueError("Summary does not match scenario outcomes")
        if (
            self.mode == "native"
            and self.binary_sha256 is None
            and any(check.status == "passed" for check in self.checks)
        ):
            raise ValueError("Native evidence requires the observed executable hash")
        if self.trace_events_seen < len(self.trace) or any(
            value < 0 for value in self.counters.values()
        ):
            raise ValueError("Invalid retained/cumulative counters")
        if any(len(note) > 600 for note in self.notes):
            raise ValueError("Note too long")
        if any(
            not math.isfinite(value) for check in self.checks for value in check.metrics.values()
        ):
            raise ValueError("Nonfinite metric")
        return self


def outcome(checks: list[Check]) -> Literal["passed", "failed", "partial"]:
    """Failed assertions dominate; missing/unsupported evidence can never produce green."""
    if any(check.status == "failed" for check in checks):
        return "failed"
    return "partial" if any(check.status == "unsupported" for check in checks) else "passed"


def dispatch_allowed(age_s: float, battery_pct: float, connected: bool) -> bool:
    """Independent reference-client gate: finite fresh arrival, connection and >=25% battery."""
    return (
        math.isfinite(age_s)
        and math.isfinite(battery_pct)
        and 0 <= age_s <= 2
        and 25 <= battery_pct <= 100
        and connected
    )


def failure_category(error: Exception, expected_running: bool, process_exited: bool):
    """A planned stopped process is not an autopilot crash; classify only observed failure facts."""
    if expected_running and process_exited:
        return "simulator"
    return "assertion" if isinstance(error, AssertionError) else "infrastructure"


def save_report(path: Path, report: Report):
    """Create new evidence exclusively; never overwrite a prior run or silently truncate payload."""
    content = report.model_dump_json(indent=2) + "\n"
    if len(content.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeds two MiB budget")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output:
        output.write(content)


def load_report(path: Path) -> Report:
    """Bound disk input before JSON/schema parsing; reject duplicate JSON keys and invalid envelopes."""
    with path.open("rb") as source:
        data = source.read(MAX_REPORT_BYTES + 1)
    return parse_report(data)


def parse_report(data: bytes | str) -> Report:
    """Apply one duplicate-key/size/schema policy to both file and downloaded-log evidence."""
    if len(data if isinstance(data, bytes) else data.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeds two MiB budget")

    def unique_keys(pairs):
        """Reject ambiguous duplicate object keys instead of accepting the last value."""
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    return Report.model_validate(json.loads(data, object_pairs_hook=unique_keys))


def synthetic_report() -> Report:
    """Return clearly labeled teaching data, never a surrogate for native CI acceptance."""
    checks = [
        Check(
            name=name,
            status="passed",
            category="behavior",
            expected="Synthetic illustrative expectation",
            observed="Synthetic illustrative result; not executed against PX4",
            elapsed_ms=1200,
            metrics={"illustrative_value": float(index + 1)},
        )
        for index, name in enumerate(SCENARIOS)
    ]
    return Report(
        run_id=str(uuid4()),
        created_utc=datetime.now(UTC).isoformat(),
        mode="synthetic",
        outcome=outcome(checks),
        version="1.17.0",
        source_commit=PINS["1.17.0"],
        checks=checks,
        observations=[
            Observation(
                at_ms=index * 1000,
                phase="nominal_mission",
                altitude_m=altitude,
                battery_pct=100 - index,
                speed_m_s=1,
                mode="MISSION" if altitude > 0 else "HOLD",
                armed=altitude > 0,
            )
            for index, altitude in enumerate([0, 2, 5, 10, 10, 6, 2, 0])
        ],
        trace_events_seen=0,
        notes=["All values are synthetic. Import a source-linked CI report for native evidence."],
    )
