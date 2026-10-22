"""Jason Stys: independent expected-versus-observed scenarios against actual owned PX4.

Classes/functions/state/variables: docs/SOURCE_MAP.md. Failed or unreached scenarios
never become green. Native paths are a separate CI gate, not mocked unit coverage.
"""

import argparse
import asyncio
import json
import time
from collections import Counter, deque
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from assurance.native import OwnedSimulator, ReferenceClient, Relay, require_unused_ports
from assurance.report import (
    PINS,
    SCENARIOS,
    Check,
    Observation,
    Report,
    dispatch_allowed,
    outcome,
    save_report,
)

EXPECTATIONS = {
    "delay": "Observed byte-preserving delivery delay >=240 ms; native telemetry recovers fresh",
    "reorder": "Observed out-of-order packet IDs with native telemetry still usable",
    "duplicate": "Observed repeated delivery of identical packet IDs; reference client remains usable",
    "blackout": "Six-second packet blackout produces stale disconnected state and dispatch denial, then fresh recovery",
    "interrupted_upload": "Lost mission ACK prevents confirmed upload; remain grounded, inspect then explicitly re-upload",
    "nominal_mission": "Actual native upload, takeoff above 3 m, HOLD, return/landing and disarm",
    "low_battery": "Actual simulated battery drops below 25%; independent dispatch gate denies start",
    "autopilot_restart": "Owned process stops, old connection expires, new session is fresh and grounded without command replay",
}


class Suite:
    """Own all resources and bounded evidence for one upstream source/build identity."""

    def __init__(self, version):
        """Allocate one source-scoped workspace and bounded observations without starting children."""
        self.version = version
        self.host = OwnedSimulator(version)
        self.relay = Relay()
        self.client = ReferenceClient()
        self.started = time.monotonic()
        self.phase = "delay"
        self.observations = deque(maxlen=200)

    async def state(self):
        """Record reported state and arrival age, keeping cached/stale values explicitly labeled."""
        self.host.healthy_process()
        if self.relay.error or self.relay.process.returncode is not None:
            raise RuntimeError("Fault relay unavailable")
        sample = await self.client.sample()
        if sample:
            self.observations.append(
                Observation(
                    at_ms=(time.monotonic() - self.started) * 1000,
                    phase=self.phase,
                    **{key: value for key, value in sample.items() if key != "healthy"},
                )
            )
        return sample

    async def wait(self, predicate, seconds=30):
        """A deadline is failed evidence, not a reason to fabricate readiness or skip an oracle."""
        deadline = time.monotonic() + seconds
        last = None
        while time.monotonic() < deadline:
            last = await self.state()
            if last and predicate(last):
                return last
            await asyncio.sleep(0.5)
        raise AssertionError(f"Native observation deadline; last state={last}")

    async def ready(self):
        """Require real position/home health, connected fresh telemetry and dispatch reserve."""
        return await self.wait(
            lambda row: (
                row["healthy"]
                and not row["armed"]
                and dispatch_allowed(row["age_s"], row["battery_pct"], row["connected"])
            ),
            90,
        )

    async def fault(self, name):
        """Measure actual C++ relay events independently of its aggregate fault counters."""
        before = self.relay.seen
        await self.relay.configure(name, 5000)
        for _ in range(6):
            await asyncio.sleep(0.5)
            await self.state()
        await self.relay.configure()
        await self.ready()
        events = list(self.relay.events)
        # Packet IDs are relay-local observations, NOT MAVLink sequence numbers.
        receives = {
            item["packet_id"]: item
            for item in events
            if item["event"] == "receive" and item["reason"] == name
        }
        sent = [item for item in events if item["event"] == "send"]
        if name == "delay":
            delays = [
                item["at_ms"] - receives[item["packet_id"]]["at_ms"]
                for item in sent
                if item["packet_id"] in receives
            ]
            assert delays and min(delays) >= 240, "No independently observed delivery delay"
            return {
                "minimum_delay_ms": float(min(delays)),
                "observed_deliveries": float(len(delays)),
            }
        if name == "duplicate":
            duplicates = Counter(
                item["packet_id"] for item in sent if item["packet_id"] in receives
            )
            count = sum(value > 1 for value in duplicates.values())
            assert count > 0, "No independently observed duplicate delivery"
            return {
                "duplicated_packets": float(count),
                "events_during_window": float(self.relay.seen - before),
            }
        inversions = 0
        for direction in ("to_sdk", "to_px4"):
            ids = [item["packet_id"] for item in sent if item["direction"] == direction]
            inversions += sum(left > right for left, right in zip(ids, ids[1:], strict=False))
        assert inversions > 0, "No independently observed reorder"
        return {"observed_order_inversions": float(inversions)}

    async def blackout(self):
        """Prove loss, denial and recovery without resending an application command."""
        before = self.client.command_count
        await self.relay.configure("blackout", 12000)
        await asyncio.sleep(6)
        lost = await self.state()
        assert lost and lost["age_s"] >= 5 and not lost["connected"], lost
        assert not dispatch_allowed(lost["age_s"], lost["battery_pct"], lost["connected"])
        await self.relay.configure()
        recovered = await self.ready()
        assert self.client.command_count == before
        return {
            "stale_age_s": lost["age_s"],
            "recovered_age_s": recovered["age_s"],
            "replayed_commands": 0.0,
        }

    async def interrupted_upload(self):
        """ACK loss creates an unconfirmed effect, not proof that the autopilot stored nothing."""
        await self.relay.configure("ack_loss", 60000)
        unconfirmed = False
        try:
            await asyncio.wait_for(self.client.upload(), 45)
        except TimeoutError:
            # An executor may still be running; fail rather than retry over an unresolved native call.
            raise AssertionError(
                "Native upload did not resolve within its failure budget"
            ) from None
        except Exception:
            unconfirmed = True
        assert unconfirmed, (
            "Upload was falsely confirmed while every downstream mission ACK was lost"
        )
        assert any(item["reason"] == "drop_ack" for item in self.relay.events), (
            "Fault did not actually drop ACKs"
        )
        sample = await self.state()
        assert sample and not sample["armed"]
        await self.relay.configure()
        stored = await self.client.mission.download_mission()
        stored_count = len(stored.mission_items)
        await (
            self.client.upload()
        )  # Explicit new action only after the failed call completed and state was inspected.
        return {
            "unconfirmed_upload": 1.0,
            "observed_stored_items": float(stored_count),
            "explicit_reupload": 1.0,
        }

    async def nominal_mission(self):
        """Observe actual movement/mode/disarm rather than treating SDK success as motion."""
        await self.ready()
        await self.client.upload()
        await self.client.command("start")
        airborne = await self.wait(lambda row: row["armed"] and row["altitude_m"] > 3, 60)
        await self.client.command("hold")
        await self.wait(lambda row: row["armed"] and row["mode"] == "HOLD", 20)
        await self.client.command("return_to_launch")
        grounded = await self.wait(lambda row: not row["armed"] and row["altitude_m"] < 2, 90)
        return {
            "takeoff_altitude_m": airborne["altitude_m"],
            "disarmed_altitude_m": grounded["altitude_m"],
        }

    async def low_battery(self):
        """Alter only PX4's actual simulator battery parameters; never inject a fake SDK percentage."""
        await self.ready()
        await self.client.param.set_param_float("SIM_BAT_MIN_PCT", 5.0)
        await self.client.param.set_param_float("SIM_BAT_DRAIN", 2.0)
        await self.client.command(
            "arm"
        )  # Grounded SIH, no mission/takeoff command in this scenario.
        low = await self.wait(lambda row: row["battery_pct"] < 25, 30)
        assert not dispatch_allowed(low["age_s"], low["battery_pct"], low["connected"])
        if low["armed"]:
            await self.client.command("disarm")
        await self.client.param.set_param_float("SIM_BAT_DRAIN", 60.0)
        await self.client.param.set_param_float("SIM_BAT_MIN_PCT", 50.0)
        await self.ready()
        return {"observed_battery_pct": low["battery_pct"], "dispatch_allowed": 0.0}

    async def autopilot_restart(self):
        """Invalidate the old SDK session and require a new observed grounded process instance."""
        await self.ready()
        old_pid = self.host.process.pid
        await self.host.stop()
        await asyncio.sleep(6)
        assert not await self.client.system.is_connected(), "Old connection did not expire"
        await self.client.close()
        await self.relay.configure()
        self.client = ReferenceClient()
        await self.host.start()
        assert self.host.process.pid != old_pid
        await self.client.open()
        await self.ready()
        await asyncio.sleep(3)
        last = await self.ready()
        assert self.client.command_count == 0 and not last["armed"]
        return {
            "owned_boot_count": float(self.host.boots),
            "replayed_commands": 0.0,
            "fresh_age_s": last["age_s"],
        }

    async def run(self):
        """Execute all required scenarios, preserving classified failure and unreached capability records."""
        checks = []
        notes = [
            "One owned simulated aircraft; no real-radio/aircraft support.",
            "ArduPilot is not implemented or validated. Imported JSON provenance is not attested.",
            "Trace timestamps use the relay's monotonic origin; observations use the Python run origin.",
            "Framing completeness does not verify CRC, MAVLink signing or identity.",
        ]
        try:
            require_unused_ports()
            await self.relay.open()
            await self.host.start()
            await self.client.open()
            await self.ready()
            for name in SCENARIOS:
                self.phase = name
                started = time.monotonic()
                metrics = (
                    await self.fault(name)
                    if name in ("delay", "reorder", "duplicate")
                    else await getattr(self, name)()
                )
                checks.append(
                    Check(
                        name=name,
                        status="passed",
                        category="behavior",
                        expected=EXPECTATIONS[name],
                        observed="Independent native observations met every scenario oracle",
                        metrics=metrics,
                        elapsed_ms=(time.monotonic() - started) * 1000,
                    )
                )
        except Exception as error:
            name = SCENARIOS[len(checks)]
            category = "assertion" if isinstance(error, AssertionError) else "infrastructure"
            if self.host.process and self.host.process.poll() is not None:
                category = "simulator"
            checks.append(
                Check(
                    name=name,
                    status="failed",
                    category=category,
                    expected=EXPECTATIONS[name],
                    observed=f"{type(error).__name__}: {str(error)[:450]}",
                    elapsed_ms=0,
                )
            )
        finally:
            for close in (self.client.close, self.host.stop, self.relay.close):
                try:
                    await close()
                except Exception as error:
                    notes.append(
                        f"Cleanup fault: {type(error).__name__}; inspect owned process diagnostics"
                    )
                    if checks and checks[-1].status == "passed":
                        checks[-1] = checks[-1].model_copy(
                            update={
                                "status": "failed",
                                "category": "infrastructure",
                                "observed": "Cleanup failed; run cannot be green",
                            }
                        )
        for name in SCENARIOS[len(checks) :]:
            checks.append(
                Check(
                    name=name,
                    status="unsupported",
                    category="capability",
                    expected=EXPECTATIONS[name],
                    observed="Not reached after a prior failure; no passing evidence",
                    elapsed_ms=0,
                )
            )
        return Report(
            run_id=str(uuid4()),
            created_utc=datetime.now(UTC).isoformat(),
            mode="native",
            outcome=outcome(checks),
            version=self.version,
            source_commit=PINS[self.version],
            binary_sha256=self.host.binary_hash,
            checks=checks,
            observations=list(self.observations),
            trace=list(self.relay.events),
            trace_events_seen=self.relay.seen,
            counters=self.relay.latest,
            notes=notes,
        )


def main():
    """Save a new report and print retrievable evidence into Actions logs without artifact uploads."""
    parser = argparse.ArgumentParser(
        description="Owned Linux PX4 assurance only; no endpoint arguments"
    )
    parser.add_argument("--version", choices=list(PINS), required=True)
    args = parser.parse_args()
    path = Path(f".runtime/report-{args.version}.json")
    if path.exists():
        raise RuntimeError("Preserve prior evidence; use a fresh runtime checkout")
    report = asyncio.run(Suite(args.version).run())
    save_report(path, report)
    print("REPORT_BEGIN")
    print(report.model_dump_json(indent=2))
    print("REPORT_END")
    summary = report.model_dump(exclude={"trace", "observations", "notes"})
    print("NATIVE_ACCEPTANCE " + json.dumps(summary))
    raise SystemExit(0 if report.outcome == "passed" else 1)


if __name__ == "__main__":
    main()
