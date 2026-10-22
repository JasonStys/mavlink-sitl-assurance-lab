/** Jason Stys: offline evidence review, honest provenance, fault timeline and accessible case inspection. Map: docs/SOURCE_MAP.md. */
import "./style.css";
import demo from "../../examples/synthetic.json";
import {
  filterChecks,
  graphPoints,
  maxBytes,
  parseReport,
  type Report,
} from "./report";

let active: Report | null = null;
const app = document.querySelector<HTMLDivElement>("#app")!;

/** Build DOM using textContent only. Uploaded strings are never interpreted as HTML or selectors. */
function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  text = "",
  className = "",
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

const header = element("header");
const brand = element("div", "SA / SITL ASSURANCE", "brand");
const boundaries = element(
  "span",
  "SIMULATION ONLY · NO AIRCRAFT ENDPOINTS",
  "boundary",
);
header.append(brand, boundaries);
const main = element("main");
main.id = "main";
const hero = element("section", "", "hero");
hero.append(
  element("p", "AUTOPILOT COMPATIBILITY / RELIABILITY", "eyebrow"),
  element("h1", "Faults are inputs. Evidence is the output."),
  element(
    "p",
    "Inspect what actually happened when a simulated link failed. Compare expected behavior with observed telemetry and packet metadata—not just a green process exit.",
    "intro",
  ),
);
const controls = element("div", "", "toolbar");
const loadDemo = element("button", "Load synthetic example");
loadDemo.type = "button";
const label = element("label", "Import local report ");
const file = element("input");
file.type = "file";
file.accept = ".json,application/json";
label.append(file);
const exportButton = element("button", "Download reviewed report");
exportButton.type = "button";
exportButton.disabled = true;
const help = element("button", "Operator guide");
help.type = "button";
controls.append(loadDemo, label, exportButton, help);
hero.append(controls);
const notice = element(
  "p",
  "Reports stay in this browser tab. No upload, telemetry service, account or external map is used.",
  "notice",
);
notice.setAttribute("role", "status");
const content = element("div");
content.id = "evidence";
const guide = element("dialog");
guide.setAttribute("aria-labelledby", "guide-title");
const guideTitle = element("h2", "How to review evidence");
guideTitle.id = "guide-title";
const closeHelp = element("button", "Close guide");
closeHelp.type = "button";
guide.append(
  guideTitle,
  element(
    "p",
    "1. Run the Linux native suite or retrieve a source-linked Actions report. Load the resulting JSON here. The example button only loads synthetic teaching data.",
  ),
  element(
    "p",
    "2. Review every expected/observed result, unsupported capability and stale sample. A failed case or a missing scenario must not be hidden by a passed summary.",
  ),
  element(
    "p",
    "3. Check the upstream commit, built executable hash and linked CI source. Imported JSON is self-reported evidence, not cryptographic provenance, certification or permission for real flight.",
  ),
  element(
    "p",
    "Packet IDs belong to this relay, not MAVLink's sequence counter. Framing completeness is not CRC or signature validation. The graph uses retained observations in order; it does not predict motion.",
  ),
  element(
    "p",
    "The native matrix covers two pinned PX4 SIH versions and one reference MAVSDK client. ArduPilot, real radios, hardware, arbitrary DUT plugins and operational resilience remain unvalidated.",
  ),
  closeHelp,
);
help.addEventListener("click", () => guide.showModal());
closeHelp.addEventListener("click", () => guide.close());
const footer = element("footer");
const author = element("a", "Built by Jason Stys");
author.href = "https://github.com/JasonStys";
author.rel = "noreferrer";
const contact = element("a", "Contact / LinkedIn");
contact.href = "https://www.linkedin.com/in/jason-stys-31b30b351/";
contact.rel = "noreferrer";
const source = element("a", "Source & documentation");
source.href = "https://github.com/JasonStys/mavlink-sitl-assurance-lab";
source.rel = "noreferrer";
footer.append(
  author,
  contact,
  source,
  element("span", "LOCAL REVIEW · ORIGINAL ENGINEERING PORTFOLIO"),
);
main.append(hero, notice, content);
app.append(header, main, footer, guide);

/** Render the entire evidence summary from validated data, not HTML embedded in a report. */
function show(report: Report): void {
  active = report;
  exportButton.disabled = false;
  content.replaceChildren();
  notice.textContent =
    report.mode === "synthetic"
      ? "SYNTHETIC EXAMPLE — illustrative values, not an executed native test."
      : "NATIVE CLAIM — verify the source-linked CI log. Imported JSON alone does not attest provenance.";
  const summary = element("section", "", "summary");
  for (const [title, value] of [
    ["Reported outcome", report.outcome.toUpperCase()],
    ["Reference autopilot", `${report.autopilot} ${report.version}`],
    [
      "Scenario evidence",
      `${report.checks.filter((check) => check.status === "passed").length} / ${report.checks.length} passed`,
    ],
    [
      "Trace retention",
      `${report.trace.length} / ${report.trace_events_seen} events`,
    ],
  ]) {
    const card = element("div", "", "metric");
    card.append(element("p", title), element("strong", value));
    summary.append(card);
  }
  const identity = element("section", "", "identity");
  identity.append(
    element("h2", "Run identity & limits"),
    element("p", `${report.created_utc} · ${report.run_id}`),
    element("p", `Source: ${report.source_commit}`, "mono"),
    element(
      "p",
      `Executable SHA-256: ${report.binary_sha256 ?? "none — synthetic example"}`,
      "mono",
    ),
    element(
      "p",
      `MAVSDK ${report.mavsdk} · ArduPilot: NOT IMPLEMENTED · no signature/encryption attestation`,
    ),
  );
  for (const note of report.notes) identity.append(element("p", note, "small"));
  const checks = element("section", "", "panel");
  const checkHeading = element("div", "", "section-head");
  checkHeading.append(element("h2", "Expected / observed"));
  const filterLabel = element("label", "Show outcomes ");
  const select = element("select");
  for (const [value, text] of [
    ["all", "All outcomes"],
    ["passed", "Passed"],
    ["failed", "Failed"],
    ["unsupported", "Unsupported / not reached"],
  ]) {
    const option = element("option", text);
    option.value = value;
    select.append(option);
  }
  filterLabel.append(select);
  checkHeading.append(filterLabel);
  checks.append(checkHeading);
  const cases = element("div");
  function renderChecks(): void {
    cases.replaceChildren();
    const filtered = filterChecks(report, select.value);
    if (!filtered.length)
      cases.append(
        element(
          "p",
          "No scenarios have this outcome. The overall summary is unchanged.",
        ),
      );
    for (const check of filtered) {
      const details = element("details", "", `case ${check.status}`);
      const title = element(
        "summary",
        `${check.name.replaceAll("_", " ")} · ${check.status.toUpperCase()} · ${(check.elapsed_ms / 1000).toFixed(2)} s`,
      );
      details.append(
        title,
        element("p", `Expected: ${check.expected}`),
        element("p", `Observed: ${check.observed}`),
        element("p", `Classification: ${check.category}`, "small"),
      );
      for (const [key, value] of Object.entries(check.metrics))
        details.append(
          element(
            "p",
            `${key}: ${Number.isInteger(value) ? value : value.toFixed(3)}`,
            "mono small",
          ),
        );
      cases.append(details);
    }
  }
  select.addEventListener("change", renderChecks);
  renderChecks();
  checks.append(cases);
  const graph = element("section", "", "panel");
  graph.append(
    element("h2", "Observed relative altitude"),
    element(
      "p",
      "Meters above reported home · retained observations in order, not a continuous flight path",
      "small",
    ),
  );
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 900 170");
  svg.setAttribute("role", "img");
  svg.setAttribute(
    "aria-label",
    "Relative altitude from retained observations; use the text table for values",
  );
  const polyline = document.createElementNS(svg.namespaceURI, "polyline");
  polyline.setAttribute(
    "points",
    graphPoints(
      report.observations.map((row) => row.altitude_m),
      Math.max(10, ...report.observations.map((row) => row.altitude_m)),
    ),
  );
  polyline.setAttribute("fill", "none");
  polyline.setAttribute("stroke", "#63e0c4");
  polyline.setAttribute("stroke-width", "3");
  svg.append(polyline);
  graph.append(svg);
  const readings = element("details");
  readings.append(
    element(
      "summary",
      `Observation table (${report.observations.length} retained)`,
    ),
  );
  const readingWrap = element("div", "", "table-wrap");
  const table = element("table");
  const headings = element("tr");
  for (const title of [
    "Elapsed s",
    "Scenario",
    "Altitude m",
    "Battery %",
    "Age s",
    "Link",
    "Mode",
  ])
    headings.append(element("th", title));
  const thead = element("thead");
  thead.append(headings);
  const tbody = element("tbody");
  for (const row of report.observations) {
    const tr = element("tr");
    for (const value of [
      (row.at_ms / 1000).toFixed(1),
      row.phase,
      row.altitude_m.toFixed(2),
      row.battery_pct.toFixed(1),
      row.age_s.toFixed(2),
      row.connected ? "connected" : "disconnected",
      row.mode,
    ])
      tr.append(element("td", value));
    tbody.append(tr);
  }
  table.append(thead, tbody);
  readingWrap.append(table);
  readings.append(readingWrap);
  graph.append(readings);
  const trace = element("section", "", "panel");
  trace.append(
    element("h2", "Packet evidence excerpt"),
    element(
      "p",
      `${report.trace.length} retained of ${report.trace_events_seen} seen. Showing the last 100 events. No payload bytes are displayed or trusted.`,
      "small",
    ),
  );
  const traceList = element("ol", "", "trace");
  for (const event of report.trace.slice(-100))
    traceList.append(
      element(
        "li",
        `${(event.at_ms / 1000).toFixed(3)} s · #${event.packet_id} · ${event.direction} · ${event.event} / ${event.reason} · IDs ${event.ids.join(", ") || "unknown"} · ${event.size} B`,
        "mono",
      ),
    );
  if (!report.trace.length)
    trace.append(element("p", "No packet trace in this synthetic example."));
  const counterList = element(
    "p",
    Object.entries(report.counters)
      .map(([key, value]) => `${key}: ${value}`)
      .join(" · "),
    "small",
  );
  trace.append(counterList, traceList);
  content.append(summary, identity, checks, graph, trace);
}

/** Read only a size-bounded selected local file; preserve the prior report if validation fails. */
file.addEventListener("change", async () => {
  const selected = file.files?.[0];
  if (!selected) return;
  try {
    if (selected.size > maxBytes) throw new Error("Report exceeds two MiB");
    show(parseReport(await selected.text()));
  } catch (error) {
    notice.textContent = `Import rejected: ${error instanceof Error ? error.message : "Invalid report"}. Previous evidence is unchanged.`;
  }
  file.value = "";
});
loadDemo.addEventListener("click", () =>
  show(parseReport(JSON.stringify(demo))),
);

/** Export only the validated in-memory report; object URLs are promptly revoked. */
exportButton.addEventListener("click", () => {
  if (!active) return;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(active, null, 2)], { type: "application/json" }),
  );
  const anchor = element("a");
  anchor.href = url;
  anchor.download = `sitl-${active.version}-${active.run_id}.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
