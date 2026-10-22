/** Jason Stys: local evidence viewer build and explicit utility coverage. Symbols: docs/SOURCE_MAP.md. */
import { defineConfig } from "vitest/config";
const policy =
  "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
export default defineConfig({
  root: "ui",
  server: {
    host: "127.0.0.1",
    headers: {
      "Content-Security-Policy": policy,
      "X-Content-Type-Options": "nosniff",
    },
  },
  preview: {
    host: "127.0.0.1",
    headers: {
      "Content-Security-Policy": policy,
      "X-Content-Type-Options": "nosniff",
    },
  },
  build: { outDir: "../dist", emptyOutDir: true },
  test: {
    include: ["src/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/report.ts"],
      reporter: ["text", "json-summary"],
      thresholds: { statements: 90, lines: 90, functions: 90, branches: 80 },
    },
  },
});
