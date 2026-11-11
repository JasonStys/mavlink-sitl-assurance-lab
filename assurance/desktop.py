"""Jason Stys: owned offline viewer launcher, bounded assets and explicit Quit. Lines: docs/SOURCE_MAP.md.

Functions/classes: read_asset, identity, Viewer, create_server, main. Variables: local token,
immutable assets, package identity and owned loopback listener. No simulator or report uploads.
"""

import argparse
import hmac
import json
import os
import platform
import re
import secrets
import stat
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from assurance import __version__

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
MAX_ASSET_BYTES = 2 * 1024 * 1024
HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def read_asset(path: Path) -> bytes:
    """Read one regular opened descriptor with a hard byte cap; never trust a prior path stat."""
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    )
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ASSET_BYTES:
            raise ValueError("Expected bounded regular asset")
        raw = stream.read(MAX_ASSET_BYTES + 1)
    if len(raw) != info.st_size or len(raw) > MAX_ASSET_BYTES:
        raise ValueError("Asset changed or exceeded its byte cap")
    return raw


def identity(root: Path) -> dict:
    """Require packaged version/source identity; an explicit source run is labeled development."""
    try:
        value = json.loads(read_asset(root / "assurance/resources/RELEASE.json"))
    except FileNotFoundError:
        if getattr(sys, "frozen", False):
            raise ValueError("Packaged identity missing") from None
        return {"name": "mavlink-sitl-assurance-lab", "version": __version__, "mode": "development"}
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value.get("schema_version") != 1
        or value.get("name") != "mavlink-sitl-assurance-lab"
        or value.get("version") != __version__
        or value.get("python_version") != platform.python_version()
        or not re.fullmatch(r"[a-f0-9]{40}", str(value.get("source_commit", "")))
        or type(value.get("source_dirty")) is not bool
    ):
        raise ValueError("Packaged identity invalid")
    return value


class Viewer(ThreadingHTTPServer):
    """Own one ephemeral loopback service and preloaded static assets, with no report storage."""

    daemon_threads = True

    def __init__(self, root: Path, port: int, metadata: dict):
        """Load only fixed production assets before opening a listener; no path-based HTTP reads."""
        self.metadata = metadata
        self.token = secrets.token_hex(32)
        self.instance = os.environ.get("PORTABLE_SMOKE_NONCE", secrets.token_hex(16))
        self.assets = {"/": (read_asset(root / "dist/index.html"), "text/html; charset=utf-8")}
        for asset in sorted((root / "dist/assets").iterdir()):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.(?:js|css)", asset.name):
                raise ValueError("Unexpected production asset")
            self.assets["/assets/" + asset.name] = (
                read_asset(asset),
                "text/javascript; charset=utf-8"
                if asset.suffix == ".js"
                else "text/css; charset=utf-8",
            )
        if len(self.assets) < 3 or len(self.assets) > 32:
            raise ValueError("Incomplete or excessive production asset set")
        super().__init__(("127.0.0.1", port), Handler)
        self.origin = f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    """Serve exact trusted routes and refuse cross-origin or unowned lifecycle actions."""

    def log_message(self, _format, *_args):
        """Avoid logging file names, report contents, lifecycle credentials or requests."""

    def reply(self, code: int, value: bytes, content_type: str = "application/json"):
        """Return bounded fixed content with restrictive headers and explicit connection closure."""
        self.send_response(code)
        for key, item in HEADERS.items():
            self.send_header(key, item)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(value)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(value)
            self.wfile.flush()
        self.close_connection = True

    def permitted(self, *, lifecycle: bool = False) -> bool:
        """Require this exact bound authority; lifecycle also requires the private constant token."""
        if self.headers.get("Host") != self.server.origin.removeprefix("http://"):
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            return False
        token = self.headers.get("X-Desktop-Token", "")
        return not lifecycle or bool(
            re.fullmatch(r"[a-f0-9]{64}", token) and hmac.compare_digest(token, self.server.token)
        )

    def do_GET(self):
        """Deliver exact assets and status; imported evidence never reaches this server."""
        if not self.permitted():
            self.reply(403, b'{"error":"Owned loopback origin required"}')
        elif self.path == "/api/health":
            self.reply(
                200,
                json.dumps(
                    {
                        "package": self.server.metadata,
                        "instance": self.server.instance,
                        "mode": "offline-viewer-only",
                    }
                ).encode(),
            )
        elif self.path == "/api/desktop/status":
            if not self.permitted(lifecycle=True):
                self.reply(403, b'{"error":"Owned application token required"}')
            else:
                self.reply(
                    200,
                    json.dumps(
                        {
                            "version": __version__,
                            "package": self.server.metadata,
                            "mode": "offline-viewer-only",
                        }
                    ).encode(),
                )
        elif self.path in self.server.assets:
            self.reply(200, *self.server.assets[self.path])
        else:
            self.reply(404, b'{"error":"Not found"}')

    do_HEAD = do_GET

    def do_POST(self):
        """Allow only this instance's explicit same-origin Quit; never accept report uploads."""
        if self.path != "/api/desktop/exit":
            self.reply(405, b'{"error":"No upload or simulator API"}')
        elif not self.permitted(lifecycle=True) or self.headers.get("Origin") != self.server.origin:
            self.reply(403, b'{"error":"Owned application token and origin required"}')
        elif (
            self.headers.get("Content-Type") != "application/json"
            or self.headers.get("Content-Length") != "17"
            or self.headers.get("Transfer-Encoding")
        ):
            self.reply(400, b'{"error":"Exact Quit confirmation required"}')
        else:
            self.connection.settimeout(2)
            try:
                valid = self.rfile.read(17) == b'{"action":"quit"}'
            except TimeoutError:
                valid = False
            if not valid:
                self.reply(400, b'{"error":"Exact Quit confirmation required"}')
            else:
                self.reply(202, b'{"stopping":true}')
                threading.Thread(target=self.server.shutdown, name="owned-viewer-stop").start()


def main(argv=None) -> int:
    """Open the complete application; --no-browser is reserved for isolated acceptance."""
    parser = argparse.ArgumentParser(description="MAVLink SITL evidence viewer by Jason Stys")
    parser.add_argument(
        "--port", type=int, choices=[0, *range(1024, 65536)], default=0, metavar="PORT"
    )
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    try:
        with Viewer(ROOT, args.port, identity(ROOT)) as server:
            url = server.origin + "/#desktop=" + server.token
            print(
                "MAVLink SITL Assurance Lab - offline evidence viewer; no simulator execution.",
                flush=True,
            )
            print(
                "PORTFOLIO_READY "
                + json.dumps(
                    {
                        "url": server.origin + "/",
                        "instance": server.instance,
                        "package": server.metadata,
                        "token": server.token,
                    }
                ),
                flush=True,
            )
            print("Open " + url + " or press Ctrl+C to stop this application.", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                print("Owner interrupt received; closing the local viewer.", flush=True)
        print("Application stopped.", flush=True)
        return 0
    except (OSError, ValueError) as error:
        print(f"Cannot start offline viewer: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
