/** Jason Stys: independently expected retained delivery cases and no-mutation checks. Map: docs/SOURCE_MAP.md. */
import { expect, test } from "vitest";
import demo from "../../examples/synthetic.json";
import { parseReport, type Trace } from "./report";
import { deliveryReview } from "./delivery";

const received: Trace = {
  event: "receive",
  phase: "delay",
  at_ms: 100,
  packet_id: 1,
  direction: "to_sdk",
  size: 12,
  reason: "delay",
  framing_complete: true,
  ids: [0],
};
const sent: Trace = { ...received, event: "send", at_ms: 160 };
test.each([
  [[received, sent, { ...sent, at_ms: 140 }], "relay-send-observed", [40, 60]],
  [[{ ...received, reason: "drop" }], "intentional-drop", []],
  [[{ ...received, reason: "drop_ack" }], "intentional-drop", []],
  [[received], "send-not-observed", []],
  [[sent], "receive-not-retained", []],
  [[received, received], "ambiguous-receive", []],
  [[received, { ...sent, at_ms: 99 }], "inconsistent-metadata", []],
  [[received, { ...sent, direction: "to_px4" }], "inconsistent-metadata", []],
  [[received, { ...sent, size: 1 }], "inconsistent-metadata", []],
  [[{ ...received, reason: "drop" }, sent], "inconsistent-metadata", []],
])("retained metadata %s gives %s", (trace, status, delays) => {
  const source = parseReport(
    JSON.stringify({ ...demo, trace, trace_events_seen: 99 }),
  );
  const before = JSON.stringify(source);
  const review = deliveryReview(source);
  expect(review.packets[0].status).toBe(status);
  expect(review.packets[0].local_delays_ms).toEqual(delays);
  expect(review.status_counts).toEqual({ [status as string]: 1 });
  expect(review.truncated).toBe(true);
  expect(JSON.stringify(source)).toBe(before);
});
test("empty trace and ordered independent IDs never infer lost packets", () => {
  expect(deliveryReview(parseReport(JSON.stringify(demo))).packets).toEqual([]);
  const source = parseReport(
    JSON.stringify({
      ...demo,
      trace: [
        received,
        { ...sent, phase: "blackout" },
        { ...received, packet_id: 2 },
      ],
      trace_events_seen: 3,
    }),
  );
  const review = deliveryReview(source);
  expect(review.truncated).toBe(false);
  expect(review.packets.map((row) => row.packet_id)).toEqual([1, 2]);
  expect(review.packets[0].phases).toEqual(["blackout", "delay"]);
  expect(review.packets[0].extra_send_count).toBe(0);
});
