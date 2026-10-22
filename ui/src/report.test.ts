/** Jason Stys: independent report integrity, schema, graph and bounded-input oracles. Map: docs/SOURCE_MAP.md. */
import { describe, it, expect } from "vitest";
import example from "../../examples/synthetic.json";
import { filterChecks, graphPoints, maxBytes, parseReport } from "./report";

/** Every case receives an independent mutable synthetic envelope, never native evidence. */
function data(): any {
  return structuredClone(example);
}

describe("report integrity", () => {
  it("rejects impossible UTC dates and preserves Unicode codepoint note limits", () => {
    const r = data();
    r.created_utc = "2026-02-31T00:00:00+00:00";
    expect(() => parseReport(JSON.stringify(r))).toThrow("calendar");
    r.created_utc = example.created_utc;
    r.notes = ["🚀".repeat(400)];
    expect(parseReport(JSON.stringify(r)).notes).toHaveLength(1);
    r.notes = ["🚀".repeat(601)];
    expect(() => parseReport(JSON.stringify(r))).toThrow();
  });
  it("round-trips the explicit synthetic example without inventing provenance", () => {
    const report = parseReport(JSON.stringify(data()));
    expect(report.mode).toBe("synthetic");
    expect(report.binary_sha256).toBeNull();
    expect(filterChecks(report, "all")).toHaveLength(8);
    expect(filterChecks(report, "failed")).toHaveLength(0);
  });
  it.each([
    (r: any) => {
      r.schema_version = 2;
    },
    (r: any) => {
      r.source_commit = "0".repeat(40);
    },
    (r: any) => {
      r.extra = "hidden";
    },
    (r: any) => {
      r.checks.pop();
    },
    (r: any) => {
      r.checks[0].name = r.checks[1].name;
    },
    (r: any) => {
      r.mode = "native";
    },
    (r: any) => {
      r.checks[0].status = "failed";
    },
    (r: any) => {
      r.checks[0].status = "unsupported";
    },
    (r: any) => {
      r.counters = { received: -1 };
    },
    (r: any) => {
      r.notes = ["x".repeat(601)];
    },
    (r: any) => {
      r.observations[0].battery_pct = 101;
    },
    (r: any) => {
      r.observations[0].armed = "false";
    },
    (r: any) => {
      r.observations[0].mode = "<script>";
    },
    (r: any) => {
      r.run_id = "wrong";
    },
    (r: any) => {
      r.checks[0].elapsed_ms = -1;
    },
    (r: any) => {
      r.checks[0].metrics = Array(21).fill(1);
    },
    (r: any) => {
      r.notes = Array(13).fill("extra");
    },
    (r: any) => {
      r.checks[0].metrics = Object.fromEntries(
        Array.from({ length: 21 }, (_, i) => [`v${i}`, i]),
      );
    },
    (r: any) => {
      r.notes = "not an array";
    },
    (r: any) => {
      delete r.trace;
    },
  ])("rejects malformed or contradictory envelope %#", (mutate) => {
    const r = data();
    mutate(r);
    expect(() => parseReport(JSON.stringify(r))).toThrow();
  });
  it("accepts failed and partial reports only with honest recomputed outcomes", () => {
    const r = data();
    r.checks[0].status = "failed";
    r.outcome = "failed";
    expect(filterChecks(parseReport(JSON.stringify(r)), "failed")).toHaveLength(
      1,
    );
    r.checks[0].status = "unsupported";
    r.outcome = "partial";
    expect(parseReport(JSON.stringify(r)).outcome).toBe("partial");
  });
  it("validates native hash, trace identifiers and retained counts", () => {
    const r = data();
    r.mode = "native";
    r.binary_sha256 = "a".repeat(64);
    r.trace = [
      {
        event: "receive",
        phase: "delay",
        at_ms: 1,
        packet_id: 1,
        direction: "to_sdk",
        size: 12,
        reason: "delay",
        framing_complete: true,
        ids: [0],
      },
    ];
    r.trace_events_seen = 1;
    expect(parseReport(JSON.stringify(r)).mode).toBe("native");
    r.trace[0].ids = [0x1000000];
    expect(() => parseReport(JSON.stringify(r))).toThrow();
    r.trace[0].ids = [0];
    r.trace_events_seen = 0;
    expect(() => parseReport(JSON.stringify(r))).toThrow();
  });
  it.each([
    "",
    "{}",
    "null",
    "[]",
    "true",
    "/*comment*/{}",
    '{"a":1,}',
    '{"a":1,"a":2}',
    " ".repeat(maxBytes + 1),
    "[".repeat(40) + "0" + "]".repeat(40),
  ])("rejects invalid or bounded raw input %#", (text) =>
    expect(() => parseReport(text)).toThrow(),
  );
  it("rejects nonfinite JSON numeric overflow and excessive syntax nodes", () => {
    const r = JSON.stringify(data()).replace(
      '"elapsed_ms":1200',
      '"elapsed_ms":1e999',
    );
    expect(() => parseReport(r)).toThrow();
    expect(() => parseReport(JSON.stringify(Array(51000).fill(0)))).toThrow();
  });
  it("plots bounded observation values without extrapolation or NaN", () => {
    expect(graphPoints([], 10)).toBe("");
    expect(graphPoints([1], 0)).toBe("");
    expect(graphPoints([NaN], 10)).toBe("");
    expect(graphPoints([1], Infinity)).toBe("");
    expect(graphPoints([-10, 5, 20], 10)).toBe("20,150 450,85 880,20");
    expect(graphPoints([5], 10)).toBe("20,85");
  });
});
