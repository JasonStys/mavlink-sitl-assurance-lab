/** Jason Stys: instance-owned desktop Quit without persisting its credential. Map: docs/SOURCE_MAP.md. */

/** Read and immediately remove the launch fragment; ordinary static viewer sessions do no fetch. */
export function takeDesktopToken(
  location: Pick<Location, "hash" | "pathname" | "search">,
  history: Pick<History, "replaceState">,
): string | null {
  const match = /^#desktop=([a-f0-9]{64})$/.exec(location.hash);
  if (!match) return null;
  history.replaceState(null, "", location.pathname + location.search);
  return match[1] ?? null;
}

/** Add lifecycle controls only after this exact compiled application's status accepts its token. */
export async function desktopControls(): Promise<void> {
  const token = takeDesktopToken(window.location, window.history);
  if (!token) return;
  const region = document.createElement("section");
  region.setAttribute("aria-label", "Desktop application");
  region.className = "notice";
  const status = document.createElement("span");
  status.setAttribute("role", "status");
  status.textContent = "Verifying the owned desktop application…";
  region.append(status);
  document.querySelector("header")?.after(region);
  try {
    const response = await fetch("/api/desktop/status", {
      headers: { "X-Desktop-Token": token },
    });
    if (!response.ok) throw new Error("Owned application status unavailable");
    const data: unknown = await response.json();
    if (
      typeof data !== "object" ||
      data === null ||
      !("version" in data) ||
      data.version !== __APP_VERSION__ ||
      !("mode" in data) ||
      data.mode !== "offline-viewer-only"
    )
      throw new Error("Application version or mode differs");
    status.textContent = `Installed evidence viewer v${__APP_VERSION__}. Imported reports remain in this tab; Linux SITL execution is separate.`;
    const quit = document.createElement("button");
    quit.type = "button";
    quit.textContent = "Quit application";
    region.append(quit);
    quit.addEventListener("click", async () => {
      if (
        !window.confirm(
          "Quit this application? Export any evidence you need first. This stops only this app's local service.",
        )
      )
        return;
      quit.disabled = true;
      try {
        const result = await fetch("/api/desktop/exit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Desktop-Token": token,
          },
          body: JSON.stringify({ action: "quit" }),
        });
        if (result.status !== 202) throw new Error("Quit was refused");
        status.textContent = "Application stopped. You may close this tab.";
      } catch {
        status.textContent =
          "Could not confirm Quit. Return to this app's console and press Ctrl+C.";
        quit.disabled = false;
      }
    });
  } catch {
    status.textContent =
      "Desktop controls unavailable. Evidence review still works; stop this app from its console with Ctrl+C.";
  }
}
