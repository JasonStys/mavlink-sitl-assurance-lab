"""Jason Stys: real extracted native viewer, negative boundaries and GUI Quit. Lines: docs/SOURCE_MAP.md.

Functions: request, main. Variables: exact package identity, nonce, owned process and local URL.
No source-server fallback, simulator, Docker, user profile reuse or external application request.
"""

import argparse
import http.client
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

if not __debug__:
    raise RuntimeError("Native acceptance refuses optimized Python")

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    """Keep all provenance/security acceptance checks active without assert optimization risk."""
    if not condition:
        raise ValueError(message)


def request(url, *, method="GET", headers=None, body=None):
    """Send only to the validated owned loopback URL; never adopt proxies or follow redirects."""
    require(
        re.fullmatch(r"http://127\.0\.0\.1:[0-9]{4,5}/[A-Za-z0-9/_-]*", url),
        "Unexpected request target",
    )
    target = urlsplit(url)
    connection = http.client.HTTPConnection("127.0.0.1", target.port, timeout=5)
    try:
        connection.request(method, target.path, body=body, headers=headers or {})
        response = connection.getresponse()
        require(not 300 <= response.status < 400, "Owned application redirected")
        raw = response.read(262145)
        require(len(raw) <= 262144, "Unexpected response size")
        return response.status, raw
    finally:
        connection.close()


def main(argv=None):
    """Own the process from fresh readiness to actual GUI shutdown; retain actual failure output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    executable = args.executable.resolve()
    expected = json.loads((executable.parent / "RELEASE.json").read_text())
    require(
        expected["name"] == "mavlink-sitl-assurance-lab" and expected["version"] == "0.2.0",
        "Wrong package",
    )
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    node = shutil.which("node")
    require(node, "QA Node runtime missing")
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "PATHEXT",
        "HOME",
        "USERPROFILE",
        "LOCALAPPDATA",
        "APPDATA",
        "PLAYWRIGHT_BROWSERS_PATH",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    windows = Path(os.environ.get("SYSTEMROOT", "C:/Windows"))
    environment["PATH"] = (
        os.pathsep.join([str(windows / "System32"), str(windows), str(Path(node).parent)])
        if os.name == "nt"
        else "/usr/bin:/bin:" + str(Path(node).parent)
    )
    nonce = secrets.token_hex(16)
    environment["PORTABLE_SMOKE_NONCE"] = nonce
    process = subprocess.Popen(
        [str(executable), "--no-browser"],
        cwd=output,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    lines, messages = queue.Queue(), []

    def drain():
        """Read readiness without arbitrary sleeps; retain private token only in memory."""
        for line in process.stdout:
            messages.append(line)
            lines.put(line.strip())

    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    token, url = "", ""
    passed = False
    try:
        deadline = time.monotonic() + 30
        while not url:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "Native readiness deadline")
            line = lines.get(timeout=remaining)
            if line.startswith("PORTFOLIO_READY "):
                ready = json.loads(line.removeprefix("PORTFOLIO_READY "))
                require(
                    ready["package"] == expected and ready["instance"] == nonce,
                    "Wrong process identity",
                )
                require(
                    re.fullmatch(r"http://127\.0\.0\.1:[0-9]{4,5}/", ready["url"]),
                    "Unexpected listener",
                )
                require(re.fullmatch(r"[a-f0-9]{64}", ready["token"]), "Missing owned token")
                url, token = ready["url"], ready["token"]
        require(process.poll() is None, "Native process exited early")
        code, raw = request(url + "api/health")
        require(
            code == 200
            and json.loads(raw)["package"] == expected
            and json.loads(raw)["instance"] == nonce,
            "Readiness did not match actual service",
        )
        require(
            request(url, headers={"Host": "foreign.invalid"})[0] == 403, "Foreign host accepted"
        )
        require(
            request(url, headers={"Origin": "https://foreign.invalid"})[0] == 403,
            "Foreign origin accepted",
        )
        require(
            request(url + "api/desktop/status", headers={"X-Desktop-Token": "0" * 64})[0] == 403,
            "Foreign token accepted",
        )
        require(
            request(
                url + "api/desktop/exit",
                method="POST",
                headers={"Content-Type": "application/json", "Origin": url.rstrip("/")},
                body=b'{"action":"quit"}',
            )[0]
            == 403,
            "Unowned Quit accepted",
        )
        require(
            request(url + "api/reports", method="POST", body=b"{}")[0] == 405,
            "Report upload accepted",
        )
        result = subprocess.run(
            [
                node,
                str(ROOT / "tools/native_feature_smoke.mjs"),
                url,
                token,
                str(executable.parent),
                str(output),
            ],
            cwd=output,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        (output / "browser.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        require(
            result.returncode == 0, "Actual compiled viewer journey failed; inspect browser.log"
        )
        require(
            process.wait(timeout=10) == 0,
            "GUI Quit did not cleanly exit the actual native application",
        )
        reader.join(timeout=5)
        require(not reader.is_alive(), "Owned output pipe remained open")
        require(
            "Application stopped." in "".join(messages), "Normal application stop was not observed"
        )
        try:
            request(url + "api/health")
        except OSError:
            pass
        else:
            raise ValueError("Service remained reachable after native exit")
        passed = True
    finally:
        forced = process.poll() is None
        if forced:
            process.terminate()
            process.wait(timeout=5)
        reader.join(timeout=5)
        if process.stdout:
            process.stdout.close()
        redacted = (
            "".join(messages).replace(token, "[ephemeral-token-redacted]")
            if token
            else "".join(messages)
        )
        (output / "service.log").write_text(redacted, encoding="utf-8")
        (output / "native.json").write_text(
            json.dumps(
                {
                    "package": expected,
                    "passed": passed,
                    "forced_cleanup": forced,
                    "actual_application_exit": process.returncode,
                    "no_developer_runtime_path": True,
                    "source_server_fallback": False,
                },
                indent=2,
            )
            + "\n"
        )
    print("Extracted native viewer import/filter/export/negative/GUI-Quit acceptance passed")


if __name__ == "__main__":
    main()
