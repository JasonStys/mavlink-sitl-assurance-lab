/** Jason Stys: real production UI import, privacy, accessibility and export journeys. Map: docs/SOURCE_MAP.md. */
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import fixture from "../../examples/synthetic.json" with { type: "json" };

test("native-shaped fixture stays unverified and trace filtering preserves exported evidence", async ({
  page,
}) => {
  // This is a browser fixture, NOT actual native acceptance; the UI must explicitly distrust its provenance.
  const report = {
    ...structuredClone(fixture),
    mode: "native",
    binary_sha256: "a".repeat(64),
    trace_events_seen: 20,
    notes: [
      "Synthetic native-shaped browser fixture; not real simulator evidence.",
    ],
    trace: [
      {
        event: "receive",
        phase: "blackout",
        at_ms: 100,
        packet_id: 21,
        direction: "to_sdk",
        size: 12,
        reason: "drop",
        framing_complete: true,
        ids: [0],
      },
      {
        event: "receive",
        phase: "interrupted_upload",
        at_ms: 200,
        packet_id: 22,
        direction: "to_sdk",
        size: 12,
        reason: "drop_ack",
        framing_complete: true,
        ids: [47],
      },
    ],
  };
  await page.goto("/");
  await page
    .getByLabel("Import local report")
    .setInputFiles({
      name: "native-shaped.json",
      mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(report)),
    });
  await expect(page.getByRole("status")).toContainText("NATIVE CLAIM");
  await expect(page.locator(".trace li")).toHaveCount(2);
  await page.getByLabel("Trace scenario").selectOption("interrupted_upload");
  await expect(page.locator(".trace li")).toHaveCount(1);
  await expect(page.locator(".trace")).toContainText("drop_ack");
  const completed = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download reviewed report" }).click();
  const path = await (await completed).path();
  expect(path).not.toBeNull();
  const saved = JSON.parse(await readFile(path!, "utf8"));
  expect(saved.trace).toHaveLength(2);
  expect(saved.trace_events_seen).toBe(20);
});

test("synthetic evidence, outcome filter, details and download work", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Download reviewed report" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Load synthetic example" }).click();
  await expect(page.getByRole("status")).toContainText("SYNTHETIC EXAMPLE");
  await expect(page.getByText("8 / 8 passed")).toBeVisible();
  await page.getByLabel("Show outcomes").selectOption("failed");
  await expect(
    page.getByText("No scenarios have this outcome.", { exact: false }),
  ).toBeVisible();
  await page.getByLabel("Show outcomes").selectOption("all");
  await page.locator("details.case summary").first().click();
  await expect(
    page.getByText("Expected: Synthetic illustrative expectation").first(),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download reviewed report" }).click();
  expect((await download).suggestedFilename()).toContain("sitl-1.17.0-");
});

test("real file input rejects false green and renders hostile strings as text", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (request) => {
    if (!request.url().startsWith("http://127.0.0.1:8851/"))
      external.push(request.url());
  });
  await page.goto("/");
  const report = structuredClone(fixture);
  report.checks[0].status = "failed";
  report.outcome = "failed";
  report.checks[0].observed =
    '<img src="https://example.invalid/track" onerror="alert(1)">';
  await page.getByLabel("Import local report").setInputFiles({
    name: "safe.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(report)),
  });
  await expect(page.getByText("FAILED", { exact: true })).toBeVisible();
  await page.locator("details.case summary").first().click();
  await expect(
    page.getByText(`Observed: ${report.checks[0].observed}`, { exact: true }),
  ).toBeVisible();
  expect(await page.locator("img").count()).toBe(0);
  report.outcome = "passed";
  await page.getByLabel("Import local report").setInputFiles({
    name: "false-green.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(report)),
  });
  await expect(page.getByRole("status")).toContainText("Import rejected");
  await expect(page.getByText("FAILED", { exact: true })).toBeVisible();
  expect(external).toEqual([]);
});

test("guide, WCAG checks, author links and narrow layout are usable", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Load synthetic example" }).click();
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
  await page.getByRole("button", { name: "Operator guide" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByRole("link", { name: "Built by Jason Stys" }),
  ).toHaveAttribute("href", "https://github.com/JasonStys");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});
