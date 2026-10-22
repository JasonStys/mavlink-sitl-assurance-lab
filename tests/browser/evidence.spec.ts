/** Jason Stys: real production UI import, privacy, accessibility and export journeys. Map: docs/SOURCE_MAP.md. */
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fixture from "../../examples/synthetic.json" with { type: "json" };

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
