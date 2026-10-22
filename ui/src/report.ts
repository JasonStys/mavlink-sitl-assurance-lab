/** Jason Stys: bounded strict JSON import, generated-schema subset interpreter and report metrics. Map: docs/SOURCE_MAP.md. */
import {
  parseTree,
  type Node as JsonNode,
  type ParseError,
} from "jsonc-parser";
import structuralSchema from "../schema/report.schema.json";

export const scenarios = [
  "delay",
  "reorder",
  "duplicate",
  "blackout",
  "interrupted_upload",
  "nominal_mission",
  "low_battery",
  "autopilot_restart",
];
export const pins: Record<string, string> = {
  "1.16.1": "94cb2012792b2ae89f0b147cfee53ee31ae550be",
  "1.17.0": "d6f12ad1c4f70ad3230afd7d86e971421e02fef4",
};
export const maxBytes = 2 * 1024 * 1024;
export type Check = {
  name: string;
  status: "passed" | "failed" | "unsupported";
  category: string;
  expected: string;
  observed: string;
  elapsed_ms: number;
  metrics: Record<string, number>;
};
export type Observation = {
  at_ms: number;
  phase: string;
  altitude_m: number;
  battery_pct: number;
  speed_m_s: number;
  mode: string;
  armed: boolean;
  age_s: number;
  connected: boolean;
};
export type Trace = {
  event: string;
  phase: string;
  at_ms: number;
  packet_id: number;
  direction: string;
  size: number;
  reason: string;
  framing_complete: boolean;
  ids: number[];
};
export type Report = {
  schema_version: 1;
  run_id: string;
  created_utc: string;
  author: string;
  mode: "native" | "synthetic";
  outcome: "passed" | "failed" | "partial";
  autopilot: string;
  version: string;
  source_commit: string;
  binary_sha256: string | null;
  mavsdk: string;
  ardupilot: string;
  checks: Check[];
  observations: Observation[];
  trace: Trace[];
  trace_events_seen: number;
  counters: Record<string, number>;
  notes: string[];
};
type Rule = {
  $defs?: Record<string, Rule>;
  $ref?: string;
  type?: string;
  anyOf?: Rule[];
  const?: unknown;
  enum?: unknown[];
  required?: string[];
  properties?: Record<string, Rule>;
  additionalProperties?: boolean | Rule;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  minItems?: number;
  maxItems?: number;
  maxProperties?: number;
  items?: Rule;
};
const schema = structuralSchema as Rule;

/** Interpret ONLY the checked-in generated schema subset, never a user-provided schema or expression. */
function conforms(value: unknown, rule: Rule, depth = 0): boolean {
  if (depth > 24) return false;
  if (rule.$ref)
    return conforms(
      value,
      schema.$defs![rule.$ref.replace("#/$defs/", "")],
      depth + 1,
    );
  if (rule.anyOf)
    return rule.anyOf.some((option) => conforms(value, option, depth + 1));
  if ("const" in rule && value !== rule.const) return false;
  if (rule.enum && !rule.enum.includes(value)) return false;
  if (rule.type === "null") return value === null;
  if (rule.type === "boolean") return typeof value === "boolean";
  if (rule.type === "number" || rule.type === "integer")
    return (
      typeof value === "number" &&
      Number.isFinite(value) &&
      (rule.type !== "integer" || Number.isInteger(value)) &&
      value >= (rule.minimum ?? -Infinity) &&
      value <= (rule.maximum ?? Infinity)
    );
  if (rule.type === "string")
    return (
      typeof value === "string" &&
      [...value].length >= (rule.minLength ?? 0) &&
      [...value].length <= (rule.maxLength ?? Infinity) &&
      (!rule.pattern || new RegExp(rule.pattern).test(value))
    );
  if (rule.type === "array")
    return (
      Array.isArray(value) &&
      value.length >= (rule.minItems ?? 0) &&
      value.length <= (rule.maxItems ?? Infinity) &&
      value.every((item) => conforms(item, rule.items!, depth + 1))
    );
  if (rule.type === "object") {
    if (value === null || typeof value !== "object" || Array.isArray(value))
      return false;
    const object = value as Record<string, unknown>;
    if (
      Object.keys(object).length > (rule.maxProperties ?? Infinity) ||
      rule.required?.some((key) => !Object.hasOwn(object, key))
    )
      return false;
    return Object.entries(object).every(([key, item]) => {
      if (rule.properties && Object.hasOwn(rule.properties, key))
        return conforms(item, rule.properties[key], depth + 1);
      if (rule.additionalProperties === false) return false;
      return typeof rule.additionalProperties === "object"
        ? conforms(item, rule.additionalProperties, depth + 1)
        : true;
    });
  }
  throw new Error(
    "Unsupported checked-in schema rule; update the reviewed interpreter",
  );
}

/** Reject duplicate keys/deep or excessive syntax trees before interpreting the bounded JSON value. */
function uniqueTree(root: JsonNode): void {
  const pending: [JsonNode, number][] = [[root, 0]];
  let count = 0;
  while (pending.length) {
    const [node, depth] = pending.pop()!;
    if (++count > 50000 || depth > 32)
      throw new Error("Report nesting/node budget exceeded");
    if (node.type === "object") {
      const names = node.children!.map(
        (property) => property.children![0].value as string,
      );
      if (new Set(names).size !== names.length)
        throw new Error("Duplicate JSON keys are not permitted");
    }
    for (const child of node.children ?? []) pending.push([child, depth + 1]);
  }
}

/** Parse a report without eval, network fetch, HTML interpretation, persistence or silent coercion. */
export function parseReport(text: string): Report {
  if (new TextEncoder().encode(text).length > maxBytes)
    throw new Error("Report exceeds two MiB");
  const errors: ParseError[] = [];
  const tree = parseTree(text, errors, {
    disallowComments: true,
    allowTrailingComma: false,
  });
  if (errors.length || !tree)
    throw new Error(
      "Select a strict JSON report, not comments or executable content",
    );
  uniqueTree(tree);
  const value: unknown = JSON.parse(text);
  if (!conforms(value, schema))
    throw new Error(
      "Report does not match schema version 1 and its bounded fields",
    );
  const report = value as Report;
  const created = new Date(report.created_utc);
  if (
    !Number.isFinite(created.getTime()) ||
    created.toISOString().slice(0, 19) !== report.created_utc.slice(0, 19)
  )
    throw new Error("Invalid UTC calendar date");
  if (report.source_commit !== pins[report.version])
    throw new Error("Version/source identity mismatch");
  const names = report.checks.map((check) => check.name);
  if (
    new Set(names).size !== scenarios.length ||
    scenarios.some((name) => !names.includes(name))
  )
    throw new Error("Every required scenario must occur exactly once");
  const derived = report.checks.some((check) => check.status === "failed")
    ? "failed"
    : report.checks.some((check) => check.status === "unsupported")
      ? "partial"
      : "passed";
  if (derived !== report.outcome)
    throw new Error("Summary contradicts scenario evidence");
  if (
    report.mode === "native" &&
    !report.binary_sha256 &&
    report.checks.some((check) => check.status === "passed")
  )
    throw new Error("Native passing evidence requires a build hash");
  if (
    report.trace_events_seen < report.trace.length ||
    Object.values(report.counters).some((value) => value < 0) ||
    report.notes.some((note) => [...note].length > 600) ||
    report.trace.some((event) =>
      event.ids.some((id) => id < 0 || id > 0xffffff),
    )
  )
    throw new Error("Invalid trace/counter/note bounds");
  return report;
}

/** Preserve input order while filtering; no case can be promoted to passed by a view filter. */
export function filterChecks(report: Report, status: string): Check[] {
  return status === "all"
    ? report.checks
    : report.checks.filter((check) => check.status === status);
}

/** Normalize finite plotted values into a compact local SVG viewport; no scientific extrapolation. */
export function graphPoints(values: number[], ceiling: number): string {
  if (
    !values.length ||
    !Number.isFinite(ceiling) ||
    ceiling <= 0 ||
    values.some((value) => !Number.isFinite(value))
  )
    return "";
  return values
    .map(
      (value, index) =>
        `${20 + (index / Math.max(1, values.length - 1)) * 860},${150 - Math.min(1, Math.max(0, value / ceiling)) * 130}`,
    )
    .join(" ");
}
