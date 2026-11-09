/** Jason Stys: actual imported relay evidence and downloadable correlation review. Map: docs/SOURCE_MAP.md. */
import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import fixture from "../../examples/synthetic.json" with { type: "json" };

test("partial relay trace exposes local sends and ambiguity without changing run outcome", async ({
  page,
}) => {
  const receive = {
    event: "receive",
    phase: "delay",
    at_ms: 100,
    packet_id: 8,
    direction: "to_sdk",
    size: 12,
    reason: "delay",
    framing_complete: true,
    ids: [0],
  };
  const source = {
    ...fixture,
    trace_events_seen: 100,
    trace: [
      receive,
      { ...receive, event: "send", at_ms: 140 },
      { ...receive, event: "send", at_ms: 160 },
      { ...receive, packet_id: 9 },
    ],
  };
  await page.goto("/");
  await page.getByLabel("Import local report").setInputFiles({
    name: "partial.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(source)),
  });
  await expect(
    page.getByRole("heading", { name: "Retained packet delivery review" }),
  ).toBeVisible();
  await expect(
    page.getByText("TRUNCATED TRACE", { exact: false }),
  ).toBeVisible();
  await expect(page.getByLabel("Retained packet correlations")).toContainText(
    "#8 · relay-send-observed · 1 receives / 2 sends · local delays 40, 60 ms",
  );
  await expect(page.getByLabel("Retained packet correlations")).toContainText(
    "#9 · send-not-observed",
  );
  await expect(page.getByText("8 / 8 passed")).toBeVisible();
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download packet review" }).click();
  const path = await (await pending).path();
  const saved = JSON.parse(await readFile(path!, "utf8"));
  expect(saved.run_id).toBe(source.run_id);
  expect(saved.packets[0].local_delays_ms).toEqual([40, 60]);
  expect(saved.packets[0].extra_send_count).toBe(1);
  expect(saved.reported_outcome).toBe("passed");
});
