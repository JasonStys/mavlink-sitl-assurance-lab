"""Jason Stys: owned PX4 processes, native MAVSDK reference client and C++ relay control.

Classes/functions/variables/lines: docs/SOURCE_MAP.md. Linux only; all paths, ports,
autostart and addresses are fixed. No remote/serial/real-aircraft attachment or DUT
plugin execution. Source/build hashes still require a trusted local OS/toolchain.
"""

import asyncio
import hashlib
import json
import math
import os
import platform
import shutil
import socket
import subprocess
import time
from collections import deque
from pathlib import Path

from assurance.report import PINS


def require_unused_ports():
    """Refuse an existing local service instead of accidentally attaching to it; not host attestation."""
    for port in (14540, 14541, 14580):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as error:
                raise RuntimeError(
                    "A fixed lab port is already owned; refusing attachment"
                ) from error


class Relay:
    """Own one fixed C++ process; retain at most 2,500 packet events and cumulative counters."""

    def __init__(self):
        """Allocate independent process/control state, bounded trace and cumulative counters."""
        self.process = None
        self.reader = None
        self.events = deque(maxlen=2500)
        self.seen = 0
        self.latest = {}
        self.control = 0
        self.ready = False
        self.error = None

    async def open(self):
        """Launch only the built lab relay; its executable accepts no endpoint arguments."""
        binary = Path(".runtime/build/fault_relay").resolve()
        self.process = await asyncio.create_subprocess_exec(
            str(binary),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self.reader = asyncio.create_task(self.drain())
        await self.until(lambda: self.ready)

    async def drain(self):
        """Drain child output continuously so a bounded excerpt cannot back-pressure simulation."""
        try:
            async for line in self.process.stdout:
                if len(line) > 8192:
                    raise RuntimeError("Relay event exceeded contract")
                item = json.loads(line)
                event = item["event"]
                if event in ("receive", "send"):
                    self.seen += 1
                    self.events.append(item)
                elif event == "control":
                    self.control = item["generation"]
                elif event == "stats":
                    self.latest = {
                        key: value for key, value in item.items() if key not in ("event", "at_ms")
                    }
                elif event == "ready":
                    self.ready = True
        except Exception as error:
            self.error = error

    async def until(self, predicate, seconds=5):
        """Bound child control waits; never reinterpret dead relay/reader as a passing test."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.error:
                raise RuntimeError("Native relay evidence reader failed") from self.error
            if self.process.returncode is not None:
                raise RuntimeError("Native relay stopped unexpectedly")
            if predicate():
                return
            await asyncio.sleep(0.02)
        raise TimeoutError("Native relay control deadline")

    async def configure(self, profile="normal", duration_ms=0):
        """Request one reviewed profile and wait for a monotonically increasing control acknowledgement."""
        if profile not in ("normal", "blackout", "delay", "reorder", "duplicate", "ack_loss"):
            raise ValueError("Unknown lab fault")
        if not isinstance(duration_ms, int) or not 0 <= duration_ms <= 60000:
            raise ValueError("Fault exceeds one-minute budget")
        previous = self.control
        self.process.stdin.write(f"profile {profile} {duration_ms}\n".encode("ascii"))
        await self.process.stdin.drain()
        await self.until(lambda: self.control > previous)

    async def snapshot(self):
        """Read a fresh cumulative counter record, separate from retained per-packet trace."""
        previous = self.latest
        self.process.stdin.write(b"stats\n")
        await self.process.stdin.drain()
        await self.until(lambda: self.latest is not previous)
        return dict(self.latest)

    async def close(self):
        """Gracefully stop only this child, then terminate/kill it if its bounded shutdown fails."""
        if self.process and self.process.returncode is None:
            self.process.stdin.write(b"quit\n")
            try:
                await self.process.stdin.drain()
                await asyncio.wait_for(self.process.wait(), 5)
            except (TimeoutError, BrokenPipeError, ConnectionResetError):
                if self.process.returncode is None:
                    self.process.terminate()
                    await self.process.wait()
        if self.reader:
            await self.reader
        if self.process and self.process.returncode != 0:
            raise RuntimeError("Owned relay failed; inspect its local diagnostics")


class ReferenceClient:
    """MAVSDK 4 native client with actual arrival timestamps and explicit command counting."""

    def __init__(self):
        """Allocate a fresh native session/cache and command counter; no connection opens here."""
        self.sdk = None
        self.values = {}
        self.times = {}
        self.tasks = []
        self.command_count = 0

    async def open(self):
        """Use the one fixed relay peer, never an IP/URL/port supplied by a caller."""
        from mavsdk import ComponentType, Configuration
        from mavsdk.asyncio import Mavsdk
        from mavsdk.asyncio.plugins.action import ActionAsync
        from mavsdk.asyncio.plugins.mission import MissionAsync
        from mavsdk.asyncio.plugins.param import ParamAsync
        from mavsdk.asyncio.plugins.telemetry import TelemetryAsync

        self.sdk = Mavsdk(Configuration.create_with_component_type(ComponentType.GROUND_STATION))
        await self.sdk.add_any_connection("udpin://127.0.0.1:14541")
        self.system = await self.sdk.first_autopilot(30)
        if (
            self.system is None
            or await self.system.get_system_id() != 1
            or await self.sdk.system_count() != 1
        ):
            raise RuntimeError("Exactly one owned simulated system with ID 1 required")
        self.telemetry = TelemetryAsync(self.system)
        self.action = ActionAsync(self.system)
        self.mission = MissionAsync(self.system)
        self.param = ParamAsync(self.system)
        await self.telemetry.set_rate_position(2)
        await self.telemetry.set_rate_velocity_ned(2)
        await self.telemetry.set_rate_battery(2)
        for key in ("position", "battery", "armed", "flight_mode", "health", "velocity_ned"):
            self.tasks.append(asyncio.create_task(self.collect(key)))

    async def collect(self, key):
        """Preserve field arrival time; reading the cache never refreshes its age."""
        async for value in getattr(self.telemetry, "subscribe_" + key)():
            self.values[key] = value
            self.times[key] = time.monotonic()

    async def sample(self):
        """Return no usable sample until actual required fields have arrived and are finite."""
        for task in self.tasks:
            if task.done():
                task.result()
                raise RuntimeError("Native subscription stopped")
        if not all(
            key in self.values
            for key in ("position", "battery", "armed", "flight_mode", "health", "velocity_ned")
        ):
            return None
        position, battery, velocity, health = (
            self.values[key] for key in ("position", "battery", "velocity_ned", "health")
        )
        numbers = (
            position.relative_altitude_m,
            battery.remaining_percent,
            velocity.north_m_s,
            velocity.east_m_s,
        )
        if (
            not all(math.isfinite(value) for value in numbers)
            or not 0 <= battery.remaining_percent <= 100
        ):
            return None
        return {
            "altitude_m": position.relative_altitude_m,
            "battery_pct": battery.remaining_percent,
            "speed_m_s": math.hypot(velocity.north_m_s, velocity.east_m_s),
            "mode": self.values["flight_mode"].name,
            "armed": self.values["armed"],
            "age_s": time.monotonic() - self.times["position"],
            "connected": await self.system.is_connected(),
            "healthy": health.is_global_position_ok and health.is_home_position_ok,
        }

    async def upload(self):
        """Upload a bounded two-point training plan; no real location or arbitrary plan input."""
        from mavsdk.plugins.mission import MissionItem, MissionPlan

        items = [
            MissionItem(
                lat,
                lon,
                10,
                3,
                True,
                math.nan,
                math.nan,
                MissionItem.CameraAction.NONE,
                math.nan,
                math.nan,
                2.0,
                math.nan,
                math.nan,
                MissionItem.VehicleAction.NONE,
            )
            for lat, lon in [(47.397742, 8.545594), (47.397922, 8.545594)]
        ]
        self.command_count += 1
        await self.mission.set_return_to_launch_after_mission(True)
        await self.mission.upload_mission(MissionPlan(items))

    async def command(self, action):
        """Explicitly invoke only reviewed reference operations; no automatic recovery replay."""
        self.command_count += 1
        if action == "start":
            await self.action.arm()
            await self.mission.start_mission()
        elif action in ("hold", "return_to_launch", "arm", "disarm"):
            await getattr(self.action, action)()
        else:
            raise ValueError("Unknown reference operation")

    async def close(self):
        """Drain all collectors before native destruction; surface faults after resources release."""
        for task in self.tasks:
            task.cancel()
        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        if self.sdk:
            self.sdk.destroy()
            self.sdk = None
        for result in results:
            if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                raise RuntimeError("Reference subscription failed") from result


class OwnedSimulator:
    """Verified source/build plus one owned SIH process; supports explicit grounded restart."""

    def __init__(self, version):
        """Select a reviewed source version and initialize owned child/log/build state."""
        self.version = version
        self.process = None
        self.log = None
        self.binary_hash = None
        self.boots = 0
        self.expected_running = False

    async def start(self):
        """Verify pinned source and launch SIH with a scrubbed fixed simulator environment."""
        if platform.system() != "Linux" or self.version not in PINS:
            raise ValueError("Only the reviewed Linux PX4 matrix is supported")
        root = Path(".runtime/px4").resolve()
        git = shutil.which("git")
        if git is None:
            raise RuntimeError("Git required to verify source")
        commit = subprocess.check_output(
            [git, "-C", str(root), "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        if commit != PINS[self.version]:
            raise RuntimeError("Upstream source identity mismatch")
        binary = root / "build/px4_sitl_default/bin/px4"
        with binary.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if self.binary_hash and digest != self.binary_hash:
            raise RuntimeError("Executable changed across restart")
        self.binary_hash = digest
        self.boots += 1
        work = root / "build/px4_sitl_default/rootfs"
        work.mkdir(parents=True, exist_ok=True)
        self.log = Path(f".runtime/px4-boot-{self.boots}.log").open("x", encoding="utf-8")
        env = {key: value for key, value in os.environ.items() if not key.startswith("PX4_")}
        env.update(
            PX4_SIM_MODEL="sihsim_quadx",
            PX4_SIMULATOR="sihsim",
            PX4_SYS_AUTOSTART="10040",
            PX4_HOME_LAT="47.397742",
            PX4_HOME_LON="8.545594",
            PX4_HOME_ALT="488",
            PX4_SIM_SPEED_FACTOR="1",
        )
        self.process = subprocess.Popen(
            [str(binary), "-d"],
            cwd=work,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=subprocess.STDOUT,
        )
        self.expected_running = True

    def healthy_process(self):
        """Distinguish a simulator crash from an assertion about the client/protocol."""
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("Owned simulator is not running")

    async def stop(self):
        """Terminate only the owned Popen child, including bounded escalation on shutdown."""
        self.expected_running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                await asyncio.to_thread(self.process.wait, 10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                await asyncio.to_thread(self.process.wait, 5)
        if self.log:
            self.log.close()
            self.log = None
