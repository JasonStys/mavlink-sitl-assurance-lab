"""Jason Stys: release version, source cleanliness and archive acceptance contracts. Lines: docs/SOURCE_MAP.md."""

import json
import subprocess
import sys

import pytest

from tools import package_app


@pytest.mark.parametrize(
    "version,level,allowed",
    [
        ((), "final", False),
        ((3, 14, 6), "final", False),
        ((3, 12, 16), "final", False),
        ((3, 14, 10), "candidate", False),
        ((3, 14, 10), "final", True),
        ((3, 14, 11), "final", True),
        ((3, 15, 0), "final", False),
    ],
)
def test_freeze_refuses_old_cached_or_prerelease_runtime(version, level, allowed):
    """A clean source checkout cannot hide an outdated or experimental embedded Python runtime."""
    assert package_app.build_python_supported(version, level) is allowed


def test_all_product_version_surfaces_agree():
    """The offline viewer product version stays distinct from imported PX4 and SDK versions."""
    assert package_app.configuration() == "0.2.0"
    fixture = json.loads((package_app.ROOT / "examples/synthetic.json").read_text())
    assert fixture["version"] == "1.17.0" and fixture["mavsdk"] == "4.0.6"


@pytest.mark.parametrize(
    "surface", ["project", "package", "lock", "lock-root", "runtime", "product"]
)
def test_mismatched_version_or_identity_cannot_build(tmp_path, surface):
    """Independent tiny real files expose any one stale or wrong product/version declaration."""
    root = package_app.ROOT
    for path in ("pyproject.toml", "package.json", "package-lock.json", "assurance/__init__.py"):
        output = tmp_path / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes((root / path).read_bytes())
    selected = {
        "project": "pyproject.toml",
        "package": "package.json",
        "lock": "package-lock.json",
        "lock-root": "package-lock.json",
        "runtime": "assurance/__init__.py",
        "product": "package.json",
    }[surface]
    path = tmp_path / selected
    if surface in {"project", "runtime"}:
        path.write_text(path.read_text().replace("0.2.0", "0.1.0"))
    else:
        value = json.loads(path.read_text())
        if surface == "lock-root":
            value["packages"][""]["version"] = "0.1.0"
        elif surface == "product":
            value["name"] = "other-project"
        else:
            value["version"] = "0.1.0"
        path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="mismatch"):
        package_app.configuration(tmp_path)


@pytest.mark.parametrize(
    "dirty,ci,override,sha,allowed",
    [
        (False, False, False, None, True),
        (True, False, False, None, False),
        (True, False, True, None, True),
        (True, True, True, "a" * 40, False),
        (False, True, True, "a" * 40, False),
        (False, True, False, "b" * 40, False),
        (False, True, False, "a" * 40, True),
    ],
)
def test_source_cleanliness_is_not_a_release_flag_waiver(
    monkeypatch, dirty, ci, override, sha, allowed
):
    """Local uncommitted candidate is explicit; CI cannot use the override or a different checkout."""

    def output(command, **_kwargs):
        return (
            "a" * 40 + "\n"
            if command[-2:] == ["rev-parse", "HEAD"]
            else " M source.py\n"
            if dirty
            else ""
        )

    monkeypatch.setattr(package_app.subprocess, "check_output", output)
    monkeypatch.setenv("GITHUB_ACTIONS", "true" if ci else "false")
    if sha:
        monkeypatch.setenv("GITHUB_SHA", sha)
    if not allowed:
        with pytest.raises(ValueError):
            package_app.source_metadata("0.2.0", allow_dirty=override)
    else:
        value = package_app.source_metadata("0.2.0", allow_dirty=override)
        assert value["source_commit"] == "a" * 40 and value["source_dirty"] is dirty


def test_archive_rejection_remains_active_with_optimized_python():
    """An actual optimized child still rejects path escape before creating any output."""
    result = subprocess.run(
        [
            sys.executable,
            "-O",
            "-c",
            "from tools.portable_archive import safe_name; safe_name('../escape', 'ExampleApp')",
        ],
        cwd=package_app.ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0 and "Unsafe archive member path" in result.stderr
