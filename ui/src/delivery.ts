/** Jason Stys: bounded retained relay correlation; no delivery or authenticity verdict. Map: docs/SOURCE_MAP.md. */
import type { Report, Trace } from "./report";

export type PacketReview = {
  packet_id: number;
  status: string;
  receive_count: number;
  send_count: number;
  extra_send_count: number;
  phases: string[];
  local_delays_ms: number[];
};

/** Keep all ambiguous metadata explicit; a relay send never proves receiver acknowledgement. */
export function deliveryReview(report: Report) {
  const groups = new Map<number, Trace[]>();
  for (const event of report.trace) {
    const group = groups.get(event.packet_id) ?? [];
    group.push(event);
    groups.set(event.packet_id, group);
  }
  const packets: PacketReview[] = [...groups.entries()]
    .sort(([a], [b]) => a - b)
    .map(([packet_id, events]) => {
      const receives = events.filter((event) => event.event === "receive");
      const sends = events.filter((event) => event.event === "send");
      let status = "send-not-observed";
      let delays: number[] = [];
      if (!receives.length) status = "receive-not-retained";
      else if (receives.length !== 1) status = "ambiguous-receive";
      else {
        const received = receives[0];
        const dropped = ["drop", "drop_ack"].includes(received.reason);
        if (
          sends.some(
            (sent) =>
              sent.direction !== received.direction ||
              sent.size !== received.size ||
              sent.at_ms < received.at_ms,
          ) ||
          (dropped && sends.length > 0)
        )
          status = "inconsistent-metadata";
        else if (dropped) status = "intentional-drop";
        else if (sends.length) {
          status = "relay-send-observed";
          delays = sends
            .map((sent) => sent.at_ms - received.at_ms)
            .sort((a, b) => a - b);
        }
      }
      return {
        packet_id,
        status,
        receive_count: receives.length,
        send_count: sends.length,
        extra_send_count: Math.max(0, sends.length - 1),
        phases: [...new Set(events.map((event) => event.phase))].sort(),
        local_delays_ms: delays,
      };
    });
  const counts: Record<string, number> = {};
  for (const packet of packets)
    counts[packet.status] = (counts[packet.status] ?? 0) + 1;
  return {
    run_id: report.run_id,
    reported_outcome: report.outcome,
    retained_events: report.trace.length,
    events_seen: report.trace_events_seen,
    truncated: report.trace_events_seen > report.trace.length,
    status_counts: Object.fromEntries(Object.entries(counts).sort()),
    packets,
    notice:
      "Retained local relay metadata only. A send is not receiver acknowledgement; absent metadata is not proof of loss. No payload, CRC, signature or authenticity verification.",
  };
}
