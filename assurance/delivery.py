"""Jason Stys: retained relay-packet correlation, not end-to-end delivery proof.

Functions, parameters and variables: docs/SOURCE_MAP.md. Never reads payloads,
changes a run outcome, dispatches a command or treats absent metadata as loss.
"""

from collections import Counter, defaultdict

from assurance.report import Report


def delivery_review(report: Report) -> dict:
    """Group bounded retained events by relay ID; disclose ambiguity and local timing only."""
    groups = defaultdict(list)
    for event in report.trace:
        groups[event.packet_id].append(event)
    packets = []
    for identifier, events in sorted(groups.items()):
        receives = [event for event in events if event.event == "receive"]
        sends = [event for event in events if event.event == "send"]
        delays = []
        if not receives:
            status = "receive-not-retained"
        elif len(receives) != 1:
            status = "ambiguous-receive"
        else:
            received = receives[0]
            inconsistent = any(
                sent.direction != received.direction
                or sent.size != received.size
                or sent.at_ms < received.at_ms
                for sent in sends
            ) or (received.reason in {"drop", "drop_ack"} and bool(sends))
            if inconsistent:
                status = "inconsistent-metadata"
            elif received.reason in {"drop", "drop_ack"}:
                status = "intentional-drop"
            elif sends:
                status = "relay-send-observed"
                delays = sorted(sent.at_ms - received.at_ms for sent in sends)
            else:
                status = "send-not-observed"
        packets.append(
            {
                "packet_id": identifier,
                "status": status,
                "receive_count": len(receives),
                "send_count": len(sends),
                "extra_send_count": max(0, len(sends) - 1),
                "phases": sorted({event.phase for event in events}),
                "local_delays_ms": delays,
            }
        )
    return {
        "run_id": report.run_id,
        "reported_outcome": report.outcome,
        "retained_events": len(report.trace),
        "events_seen": report.trace_events_seen,
        "truncated": report.trace_events_seen > len(report.trace),
        "status_counts": dict(sorted(Counter(row["status"] for row in packets).items())),
        "packets": packets,
        "notice": "Retained local relay metadata only. A send is not receiver acknowledgement; absent metadata is not proof of loss. No payload, CRC, signature or authenticity verification.",
    }
