/** Jason Stys: lifecycle fragment privacy and ordinary static-viewer behavior. Map: docs/SOURCE_MAP.md. */
import { describe, expect, it } from "vitest";
import { takeDesktopToken } from "./desktop";

describe("desktop credential lifecycle", () => {
  it("removes the exact token from the address before any asynchronous work", () => {
    const calls: unknown[][] = [];
    const token = "a".repeat(64);
    expect(
      takeDesktopToken(
        { hash: "#desktop=" + token, pathname: "/", search: "" },
        { replaceState: (...args) => calls.push(args) },
      ),
    ).toBe(token);
    expect(calls).toEqual([[null, "", "/"]]);
  });
  it.each([
    "",
    "#main",
    "#desktop=short",
    "#desktop=" + "A".repeat(64),
    "#desktop=" + "a".repeat(65),
  ])("ignores ordinary or malformed fragment %s", (hash) => {
    let calls = 0;
    expect(
      takeDesktopToken(
        { hash, pathname: "/", search: "" },
        {
          replaceState: () => {
            calls += 1;
          },
        },
      ),
    ).toBeNull();
    expect(calls).toBe(0);
  });
});
