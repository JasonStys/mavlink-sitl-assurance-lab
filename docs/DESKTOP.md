# Desktop evidence viewer

The 0.2.0 application candidate packages this project's complete offline report
viewer. A portable download contains its Python runtime, production web assets,
original optional example and license notices. It does **not** contain PX4,
MAVSDK, the Linux UDP relay, a flight controller or simulator execution service.
The existing Linux native suite and its two-version CI remain separate.

## Open, review and stop

Extract the complete archive into a new folder and open `MavlinkEvidenceStudio`
(`MavlinkEvidenceStudio.exe` on Windows). Keep its internal files together.
The application chooses a fresh loopback port and opens your normal browser.
No account, system Python, Node, Docker or compiler is needed to use a built
package. Source builds still need the pinned development tools.

Use **Import local report** for any valid supported report JSON, not just the
prepared example. Filter outcomes, expand expected/observed checks and inspect
packet correlations. **Download reviewed report** retains the complete validated
input even when the display is filtered. **Download packet review** exports the
derived local receive/send correlation. Neither export proves payload identity,
receiver acknowledgement or a native run's authenticity.

A malformed import displays its error and retains the previous validated report.
The error notice makes that distinction explicit. Do not confuse previously
displayed evidence with a rejected newer file. Reports stay in that browser tab:
the native service has no report-upload endpoint or persistent report store.
Closing the tab discards its in-memory work unless you exported it.

Choose **Quit application** and confirm to stop only this launch's local service.
The launch credential is held in memory, removed from the address before status
requests, never stored in browser storage, and never part of exported reports.
You can also return to this application's console and press Ctrl+C. Closing only
the browser does not stop the service. A second launch owns a separate port and
credential rather than adopting another service.

If the browser does not open, use the URL printed in this application's console.
Treat the temporary fragment as a local control credential. These unsigned
portable packages do not constitute a managed installer, signed publisher
identity, mobile app, upgrade transaction or uninstall registration.

## Build and validate

From an authorized source checkout:

Use final Python **3.14.10 or a later 3.14 security patch** for packaging. The
builder rejects older cached runtimes and prereleases, and the application checks
its recorded Python version against its actual embedded interpreter. Development
compatibility and the Linux simulator matrix remain separate from this freeze rule.

```text
python -m pip install --require-hashes -r requirements.lock
python -m pip install --require-hashes -r requirements-package.lock
npm ci --ignore-scripts
npm run build
npx playwright install chromium
python tools/package_app.py
```

The builder creates one version/OS/architecture archive and SHA256 sidecar only
after safe extraction and actual compiled GUI import/filter/export/negative/Quit
acceptance. Windows uses ZIP; POSIX uses tar.gz to preserve internal relative
links and execute permissions. Existing archive or checksum destinations are
never overwritten. Build objects and outputs stay under ignored `.runtime/`.

Hosted builds require clean exact checked-out source. A developer may explicitly
use `--allow-dirty` locally; that labels the package `source_dirty: true` and is
forbidden in CI. Such a candidate is not an immutable release. No build command
creates a release, retargets a tag or publishes assets.

The source viewer remains available with the existing npm instructions. With a
built UI, `python -m assurance.desktop --no-browser` exercises the local source
launcher without opening a browser; it is labeled development, not a release.

## Scope of acceptance

Native package checks run the actual extracted executable from an unrelated
directory with developer runtimes removed from PATH. They import a changed valid
synthetic report, verify a failed-case filter, compare both downloads to independent
expected values, reject malformed import and unowned Quit, and confirm real GUI
Quit exits the process. They do not run PX4 or claim a clean-system installer,
manual default-browser compatibility, signed distribution or real aircraft use.
