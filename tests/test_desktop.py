"""Jason Stys: actual local viewer boundaries and supported owned exit. Lines: docs/SOURCE_MAP.md."""

import http.client
import json
import platform
import stat
import threading
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from assurance import desktop


@pytest.fixture
def bundle(tmp_path):
    """Create inert production-shaped unit assets; compiled acceptance is a separate real executable."""
    (tmp_path / "dist/assets").mkdir(parents=True)
    (tmp_path / "dist/index.html").write_text("<h1>Offline review</h1>")
    (tmp_path / "dist/assets/main-abc.js").write_text("export const x=1;")
    (tmp_path / "dist/assets/main-abc.css").write_text("body{color:black}")
    return tmp_path


@contextmanager
def running(bundle):
    """Own one real port0 test listener and join its exact thread without sleeps or server reuse."""
    server = desktop.Viewer(bundle, 0, desktop.identity(bundle))
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        yield server, thread
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def call(server, path="/", *, method="GET", headers=None, body=None):
    """Make an actual bounded HTTP request to this fixture's exact listener."""
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_complete_assets_status_no_upload_and_owned_quit(bundle):
    """Serve actual bytes; arbitrary report POST is refused; explicit owned Quit ends its loop."""
    with running(bundle) as (server, thread):
        for route, expected in [("/", b"Offline review"), ("/assets/main-abc.js", b"export const")]:
            code, headers, body = call(server, route)
            assert code == 200 and expected in body
            assert headers["Cache-Control"] == "no-store"
            assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
            assert server.token.encode() not in body
        assert call(server, method="HEAD")[2] == b""
        health = json.loads(call(server, "/api/health")[2])
        assert (
            health["mode"] == "offline-viewer-only" and health["package"]["mode"] == "development"
        )
        assert "token" not in health
        assert call(server, "/api/desktop/status")[0] == 403
        authorized = {"X-Desktop-Token": server.token}
        status = json.loads(call(server, "/api/desktop/status", headers=authorized)[2])
        assert status["version"] == "0.2.0" and status["mode"] == "offline-viewer-only"
        assert call(server, "/api/reports", method="POST", body=b"{}")[0] == 405
        assert call(server, "/api/desktop/exit")[0] == 404
        authorized.update({"Origin": server.origin, "Content-Type": "application/json"})
        result = call(
            server,
            "/api/desktop/exit",
            method="POST",
            headers=authorized,
            body=b'{"action":"quit"}',
        )
        assert result[0] == 202 and json.loads(result[2]) == {"stopping": True}
        thread.join(timeout=5)
        assert not thread.is_alive()


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "evil.example"},
        {"Host": "localhost:1234"},
        {"Origin": "https://foreign.invalid"},
    ],
)
def test_foreign_authority_or_origin_rejected(bundle, headers):
    """A local TCP connection cannot borrow another authority or browser origin."""
    with running(bundle) as (server, _):
        assert call(server, headers=headers)[0] == 403


@pytest.mark.parametrize(
    "route",
    ["/../requirements.lock", "/assets/../index.html", "/?x=1", "/assets/missing.js", "/api/run"],
)
def test_fixed_routes_never_read_caller_paths(bundle, route):
    """No path/query fallback exposes the source tree or a simulator interface."""
    with running(bundle) as (server, _):
        assert call(server, route)[0] == 404


@pytest.mark.parametrize(
    "kind,body,expected",
    [
        ("missing-token", b'{"action":"quit"}', 403),
        ("wrong-token", b'{"action":"quit"}', 403),
        ("missing-origin", b'{"action":"quit"}', 403),
        ("foreign-origin", b'{"action":"quit"}', 403),
        ("wrong-type", b'{"action":"quit"}', 400),
        ("different-length", b"{}", 400),
        ("different-action", b'{"action":"nope"}', 400),
        ("transfer-encoding", b'{"action":"quit"}', 400),
    ],
)
def test_quit_negatives_leave_application_running(bundle, kind, body, expected):
    """Missing/foreign credentials and malformed confirmation never stop another app instance."""
    with running(bundle) as (server, thread):
        headers = {
            "X-Desktop-Token": server.token,
            "Origin": server.origin,
            "Content-Type": "application/json",
        }
        if kind == "missing-token":
            headers.pop("X-Desktop-Token")
        elif kind == "wrong-token":
            headers["X-Desktop-Token"] = "0" * 64
        elif kind == "missing-origin":
            headers.pop("Origin")
        elif kind == "foreign-origin":
            headers["Origin"] = "https://foreign.invalid"
        elif kind == "wrong-type":
            headers["Content-Type"] = "text/plain"
        elif kind == "transfer-encoding":
            headers["Transfer-Encoding"] = "chunked"
        assert (
            call(server, "/api/desktop/exit", method="POST", headers=headers, body=body)[0]
            == expected
        )
        assert thread.is_alive() and call(server, "/api/health")[0] == 200


def test_tokens_are_per_instance(bundle):
    """Two independent opens cannot use one another's Quit credential."""
    with running(bundle) as (one, _), running(bundle) as (two, _):
        assert one.token != two.token and one.server_port != two.server_port
        assert call(two, "/api/desktop/status", headers={"X-Desktop-Token": one.token})[0] == 403


def test_package_identity_and_source_mode(bundle, monkeypatch):
    """Missing frozen identity is a hard error; source runs cannot masquerade as a release."""
    assert desktop.identity(bundle)["mode"] == "development"
    monkeypatch.setattr(desktop.sys, "frozen", True, raising=False)
    with pytest.raises(ValueError, match="missing"):
        desktop.identity(bundle)
    path = bundle / "assurance/resources/RELEASE.json"
    path.parent.mkdir(parents=True)
    value = {
        "schema_version": 1,
        "name": "mavlink-sitl-assurance-lab",
        "version": "0.2.0",
        "source_commit": "a" * 40,
        "source_dirty": False,
        "python_version": platform.python_version(),
    }
    path.write_text(json.dumps(value))
    assert desktop.identity(bundle) == value
    for key, bad in [
        ("schema_version", 2),
        ("name", "other"),
        ("version", "0.1.0"),
        ("source_commit", "main"),
        ("source_dirty", 0),
        ("python_version", "0.0.0"),
    ]:
        path.write_text(json.dumps({**value, key: bad}))
        with pytest.raises(ValueError, match="invalid"):
            desktop.identity(bundle)


def test_asset_descriptor_cap_change_and_nonregular(bundle, monkeypatch):
    """Real reads are bounded; opened descriptor identity and actual byte length are both checked."""
    path = bundle / "dist/index.html"
    assert desktop.read_asset(path).startswith(b"<h1>")
    monkeypatch.setattr(desktop, "MAX_ASSET_BYTES", 4)
    with pytest.raises(ValueError, match="bounded"):
        desktop.read_asset(path)
    monkeypatch.setattr(
        desktop.os, "fstat", lambda _fd: SimpleNamespace(st_mode=stat.S_IFIFO, st_size=0)
    )
    with pytest.raises(ValueError, match="bounded"):
        desktop.read_asset(path)
    monkeypatch.setattr(
        desktop.os, "fstat", lambda _fd: SimpleNamespace(st_mode=stat.S_IFREG, st_size=1)
    )
    with pytest.raises(ValueError, match="changed"):
        desktop.read_asset(path)


def test_bad_or_missing_asset_sets_fail_before_listener(bundle):
    """Unexpected files or incomplete build never open an apparently healthy empty viewer."""
    (bundle / "dist/assets/foreign.map").write_text("unsupported")
    with pytest.raises(ValueError, match="Unexpected"):
        desktop.Viewer(bundle, 0, {})
    (bundle / "dist/assets/foreign.map").unlink()
    (bundle / "dist/assets/main-abc.css").unlink()
    with pytest.raises(ValueError, match="Incomplete"):
        desktop.Viewer(bundle, 0, {})


@pytest.mark.parametrize("no_browser", [False, True])
def test_source_launcher_opener_and_ctrl_c_control_flow(bundle, monkeypatch, capsys, no_browser):
    """Unit-test launch options; actual compiled GUI Quit is separately exercised by native acceptance."""
    calls = []

    class ControlledViewer:
        origin = "http://127.0.0.1:45678"
        token = "a" * 64
        instance = "b" * 32
        metadata = {"mode": "development"}

        def __init__(self, root, port, metadata):
            assert root == bundle and port == 0 and metadata["mode"] == "development"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            calls.append("closed")

        def serve_forever(self, **_kwargs):
            raise KeyboardInterrupt()

    monkeypatch.setattr(desktop, "ROOT", bundle)
    monkeypatch.setattr(desktop, "Viewer", ControlledViewer)
    monkeypatch.setattr(desktop.webbrowser, "open", lambda value: calls.append(value))
    assert desktop.main(["--no-browser"] if no_browser else []) == 0
    assert calls == (
        ["closed"] if no_browser else ["http://127.0.0.1:45678/#desktop=" + "a" * 64, "closed"]
    )
    assert "Application stopped." in capsys.readouterr().out


def test_source_launcher_missing_build_and_privileged_port_fail_closed(
    tmp_path, monkeypatch, capsys
):
    """A missing build cannot open a browser; privileged or out-of-range ports are rejected."""
    monkeypatch.setattr(desktop, "ROOT", tmp_path)
    assert desktop.main(["--no-browser"]) == 1
    assert "Cannot start offline viewer" in capsys.readouterr().err
    for port in ("80", "-1", "65536"):
        with pytest.raises(SystemExit):
            desktop.main(["--port", port])
