/** Jason Stys: actual extracted application file/review/export/Exit journey. Map: docs/SOURCE_MAP.md. */
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const [raw, token, bundle, output] = process.argv.slice(2);
const url = new URL(raw);
assert.equal(url.hostname, "127.0.0.1");
assert.equal(url.protocol, "http:");
assert.match(token ?? "", /^[a-f0-9]{64}$/);
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    baseURL: url.href,
    acceptDownloads: true,
    viewport: { width: 1440, height: 1000 },
  });
  context.setDefaultTimeout(8000);
  const external = [],
    errors = [];
  await context.route("**/*", (route) => {
    if (new URL(route.request().url()).origin !== url.origin) {
      external.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(url.href + "#desktop=" + token);
  await expect(
    page.getByRole("region", { name: "Desktop application" }),
  ).toHaveCount(1);
  await expect(page.getByLabel("Desktop application")).toContainText(
    "Installed evidence viewer v0.2.0",
  );
  assert.equal(new URL(page.url()).hash, "");
  const report = JSON.parse(
    await readFile(
      path.join(bundle, "_internal/examples/synthetic.json"),
      "utf8",
    ),
  );
  report.run_id = "00000000-0000-4000-8000-000000000777";
  report.outcome = "failed";
  report.checks[0].status = "failed";
  report.checks[0].category = "assertion";
  report.checks[0].observed =
    "Synthetic custom imported failure; no autopilot execution.";
  const receive = {
    event: "receive",
    phase: "delay",
    at_ms: 100,
    packet_id: 77,
    direction: "to_sdk",
    size: 12,
    reason: "delay",
    framing_complete: true,
    ids: [0],
  };
  report.trace = [receive, { ...receive, event: "send", at_ms: 140 }];
  report.trace_events_seen = 2;
  await page.getByLabel("Import local report").setInputFiles({
    name: "custom-review.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(report)),
  });
  await expect(page.getByText(report.run_id, { exact: false })).toBeVisible();
  await expect(page.getByLabel("Retained packet correlations")).toContainText(
    "#77 · relay-send-observed · 1 receives / 1 sends · local delays 40 ms",
  );
  await page.getByLabel("Show outcomes").selectOption("failed");
  await expect(page.locator("#evidence details").first()).toContainText(
    "delay · FAILED",
  );
  assert.deepEqual(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
        .analyze()
    ).violations,
    [],
  );
  assert.equal(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
    0,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    true,
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download reviewed report", exact: true })
    .click();
  const exported = JSON.parse(
    await readFile(await (await download).path(), "utf8"),
  );
  assert.deepEqual(exported, report);
  const packetDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download packet review" }).click();
  const review = JSON.parse(
    await readFile(await (await packetDownload).path(), "utf8"),
  );
  assert.deepEqual(review.packets[0].local_delays_ms, [40]);
  assert.equal(review.run_id, report.run_id);
  await page.screenshot({
    path: path.join(output, "01-imported-failed-report.png"),
    fullPage: true,
  });
  await page.getByLabel("Import local report").setInputFiles({
    name: "bad.json",
    mimeType: "application/json",
    buffer: Buffer.from('{"invalid":true}'),
  });
  await expect(
    page.getByText("Import rejected:", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText(report.run_id, { exact: false })).toBeVisible();
  const pending = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download reviewed report", exact: true })
    .click();
  assert.deepEqual(
    JSON.parse(await readFile(await (await pending).path(), "utf8")),
    report,
  );
  await page.getByRole("button", { name: "Operator guide" }).click();
  await expect(page.getByRole("dialog")).toContainText("Linux native suite");
  await page.getByRole("button", { name: "Close guide" }).click();
  await page
    .locator("#evidence section")
    .last()
    .screenshot({ path: path.join(output, "02-packet-review.png") });
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.getByRole("button", { name: "Quit application" }).click();
  assert.equal((await context.request.get("/api/health")).status(), 200);
  await expect(
    page.getByRole("button", { name: "Quit application" }),
  ).toBeEnabled();
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Quit application" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Desktop application")).toContainText(
    "Application stopped",
  );
  assert.deepEqual(external, []);
  assert.deepEqual(errors, []);
  await writeFile(
    path.join(output, "feature.json"),
    JSON.stringify(
      {
        arbitrary_supported_import: true,
        filtered_failed_case: true,
        report_export_exact: true,
        packet_id: 77,
        local_delay_ms: 40,
        invalid_import_preserved_prior: true,
        gui_exit_confirmed: true,
        no_external_requests: true,
      },
      null,
      2,
    ) + "\n",
    { flag: "wx" },
  );
  await context.close();
} finally {
  await browser.close();
}
