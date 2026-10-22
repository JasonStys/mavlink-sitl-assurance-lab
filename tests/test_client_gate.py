"""Jason Stys: isolated reference API dispatch-order oracles, NOT actual SDK/flight evidence.

Functions/variables/lines: docs/SOURCE_MAP.md. Synthetic cached states exercise the
real reference methods without launching a binary, opening a socket or mocking a
native compatibility pass. Real SDK behavior remains a separate mandatory CI gate.
"""

import asyncio
from types import SimpleNamespace

import pytest

from assurance.native import ReferenceClient
from assurance.report import DispatchDenied


@pytest.mark.parametrize(
    "change",
    [
        None,
        {"age_s": 3},
        {"battery_pct": 24},
        {"connected": False},
        {"armed": True},
        {"healthy": False},
    ],
)
@pytest.mark.parametrize("operation", ["start", "arm", "upload"])
def test_reference_api_denies_before_sdk_effect(change, operation):
    """Every unsafe dispatch exits before a plugin is even needed and before counter increment."""

    async def scenario():
        client = ReferenceClient()

        async def sample():
            if change is None:
                return None
            return {
                "age_s": 0.5,
                "battery_pct": 90,
                "connected": True,
                "armed": False,
                "healthy": True,
                **change,
            }

        client.sample = sample
        with pytest.raises(DispatchDenied):
            if operation == "upload":
                await client.upload()
            else:
                await client.command(operation)
        assert client.command_count == 0

    asyncio.run(scenario())


def test_valid_reference_start_has_explicit_order_and_unknown_action_no_effect():
    """A valid start arms then starts once; arbitrary action strings do not invoke a plugin."""
    calls = []

    async def scenario():
        client = ReferenceClient()

        async def sample():
            return {
                "age_s": 0.5,
                "battery_pct": 90,
                "connected": True,
                "armed": False,
                "healthy": True,
            }

        async def arm():
            calls.append("arm")

        async def start():
            calls.append("start")

        client.sample = sample
        client.action = SimpleNamespace(arm=arm)
        client.mission = SimpleNamespace(start_mission=start)
        await client.command("start")
        with pytest.raises(ValueError, match="Unknown"):
            await client.command("shell")
        assert client.command_count == 1

    asyncio.run(scenario())
    assert calls == ["arm", "start"]
