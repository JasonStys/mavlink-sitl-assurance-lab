/** Jason Stys: actual production evidence-viewer journeys across three browser engines. Map: docs/SOURCE_MAP.md. */
import { defineConfig, devices } from "@playwright/test";
const port = Number(process.env.SITL_REVIEW_TEST_PORT ?? 8851);
export default defineConfig({
  testDir: "tests/browser",
  workers: 1,
  retries: 0,
  timeout: 30000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    reducedMotion: "reduce",
    trace: "retain-on-failure",
  },
  reporter: "list",
  webServer: {
    command: `npm run preview -- --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    timeout: 30000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
