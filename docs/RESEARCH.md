# Primary sources and attribution

By Jason Stys. Reviewed 2026-10-21/22; documentation evolves, runtime source pins do not.

- [PX4 simulation](https://docs.px4.io/main/en/simulation/) and
  [SIH](https://docs.px4.io/main/en/sim_sih/): real autopilot simulation, not a UI animation.
  The exact reviewed releases use the `px4_sitl_default` build and SIH autostart10040.
- [PX4 1.16.1 source](https://github.com/PX4/PX4-Autopilot/tree/94cb2012792b2ae89f0b147cfee53ee31ae550be)
  and [1.17.0 source](https://github.com/PX4/PX4-Autopilot/tree/d6f12ad1c4f70ad3230afd7d86e971421e02fef4):
  compatibility matrix is tied to commits, not moving branch/release names.
- [Actual simulator battery parameters](https://github.com/PX4/PX4-Autopilot/blob/v1.17.0/src/modules/simulation/battery_simulator/battery_simulator_params.c)
  and [implementation](https://github.com/PX4/PX4-Autopilot/blob/v1.17.0/src/modules/simulation/battery_simulator/BatterySimulator.cpp):
  drain occurs while armed; disarm resets the simulated battery. Tests change only
  those owned simulator parameters rather than inventing SDK observations.
- [Native MAVSDK Python](https://mavsdk.mavlink.io/main/en/python/quickstart.html) and
  [4.0.6 telemetry source](https://github.com/mavlink/MAVSDK/blob/v4.0.6/cpp/src/mavsdk/plugins/telemetry/telemetry_impl.cpp):
  native C++ binding, not legacy gRPC API; remaining battery is 0–100 percentage points.
- [MAVLink serialization](https://mavlink.io/en/guide/serialization.html),
  [mission protocol](https://mavlink.io/en/services/mission.html), and
  [security FAQ](https://mavlink.io/en/about/faq.html): v1/v2 framing, mission acknowledgement,
  retransmission and the distinction between signing and confidentiality. This lab's
  framing inspection is deliberately not CRC/signature/authentication verification.
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) and
  [JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/): canonical bounded
  serialization contract; a reviewed browser subset is explicitly not a full schema engine.
- [jsonc-parser](https://github.com/microsoft/node-jsonc-parser): syntax-tree inspection;
  comments/trailing commas disabled and duplicate keys checked independently.
- [OWASP DOM XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html):
  use text-only DOM APIs rather than interpreting uploaded HTML.

All example data and original lab code are created for this portfolio. Upstream PX4,
MAVSDK and dependencies keep independent licenses/copyrights. No employer endorsement,
private/customer flight records, actual incident/person locations, scraped imagery,
military certification or real-aircraft capability is implied.
