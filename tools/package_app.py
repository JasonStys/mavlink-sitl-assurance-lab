"""Jason Stys: native offline viewer build, safe archive and extracted acceptance. Lines: docs/SOURCE_MAP.md.

Functions: configuration, source_metadata, main. Variables: clean source/version identity,
owned build directories and exactly one archive/checksum pair. No release or tag mutation.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from importlib.metadata import distribution
from pathlib import Path

if __package__:
    from .portable_archive import archive_metadata, create_archive, extract_archive, require
else:
    from portable_archive import archive_metadata, create_archive, extract_archive, require

ROOT = Path(__file__).resolve().parents[1]
APPLICATION = "MavlinkEvidenceStudio"
PRODUCT = "mavlink-sitl-assurance-lab"


def build_python_supported(version: tuple[int, ...], releaselevel: str) -> bool:
    """Freeze only a final Python3.14 runtime at the current security-patch floor or later."""
    return (
        len(version) >= 3
        and version[:2] == (3, 14)
        and version[2] >= 10
        and releaselevel == "final"
    )


def configuration(root: Path = ROOT) -> str:
    """Require coherent metadata before building; the application version is not the PX4 version."""
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    package = json.loads((root / "package.json").read_text())
    lock = json.loads((root / "package-lock.json").read_text())
    version = project["version"]
    require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version), "Invalid version")
    require(project["name"] == package["name"] == lock["name"] == PRODUCT, "Product mismatch")
    require(
        version == package["version"] == lock["version"] == lock["packages"][""]["version"],
        "Version mismatch",
    )
    require(
        f'__version__ = "{version}"' in (root / "assurance/__init__.py").read_text(),
        "Runtime version mismatch",
    )
    return version


def source_metadata(version: str, *, allow_dirty: bool = False) -> dict:
    """Label local candidates honestly; hosted builds always require exact clean checked-out source."""
    require(
        not allow_dirty or os.environ.get("GITHUB_ACTIONS") != "true",
        "Dirty override forbidden in CI",
    )
    command = ["git", "-c", "safe.directory=" + ROOT.as_posix(), "-C", str(ROOT)]
    source = subprocess.check_output([*command, "rev-parse", "HEAD"], text=True).strip()
    changed = subprocess.check_output(
        [*command, "status", "--porcelain", "--untracked-files=all"], text=True
    )
    require(re.fullmatch(r"[a-f0-9]{40}", source), "Invalid source identity")
    require(
        not changed or (allow_dirty and os.environ.get("GITHUB_ACTIONS") != "true"),
        "Clean source required; local candidate override is never allowed in CI",
    )
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(os.environ.get("GITHUB_SHA") == source, "CI checkout identity mismatch")
    return {
        "schema_version": 1,
        "name": PRODUCT,
        "version": version,
        "source_commit": source,
        "source_dirty": bool(changed),
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "python_version": platform.python_version(),
    }


def main(argv=None) -> int:
    """Build and test the archive actually produced; no source-server fallback or existing target reuse."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / ".runtime/portable")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Label a local uncommitted candidate; forbidden in CI",
    )
    args = parser.parse_args(argv)
    require(
        build_python_supported(tuple(sys.version_info[:3]), sys.version_info.releaselevel),
        "Freeze requires final Python 3.14.10 or a later 3.14 security patch",
    )
    version = configuration()
    metadata = source_metadata(version, allow_dirty=args.allow_dirty)
    require((ROOT / "dist/index.html").is_file(), "Build the production viewer first")
    generated = ROOT / ".runtime/package-meta"
    generated.mkdir(parents=True, exist_ok=True)
    identity_file = generated / "RELEASE.json"
    identity_file.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    pyinstaller = distribution("pyinstaller")
    licenses = [
        pyinstaller.locate_file(path)
        for path in pyinstaller.files or []
        if str(path).endswith("licenses/COPYING.txt")
    ]
    require(len(licenses) == 1, "Exact PyInstaller notice missing")
    build = ROOT / ".runtime/packaged"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console",
        "--name",
        APPLICATION,
        "--distpath",
        str(build),
        "--workpath",
        str(ROOT / ".runtime/pyinstaller"),
        "--specpath",
        str(ROOT / ".runtime"),
    ]
    for source, destination in [
        ("dist", "dist"),
        ("examples/synthetic.json", "examples"),
        ("LICENSE", "licenses/project"),
        ("licenses/PYTHON.txt", "licenses/python"),
        ("licenses/JSONC-PARSER.txt", "licenses/jsonc-parser"),
        (str(licenses[0]), "licenses/pyinstaller"),
        (str(identity_file), "assurance/resources"),
    ]:
        source_path = Path(source)
        if not source_path.is_absolute():
            source_path = ROOT / source_path
        command += ["--add-data", str(source_path) + ":" + destination]
    command += ["launcher.py"]
    environment = {**os.environ, "PYINSTALLER_CONFIG_DIR": str(ROOT / ".runtime/pyinstaller-cache")}
    subprocess.run(command, cwd=ROOT, env=environment, check=True, timeout=600)
    require(
        source_metadata(version, allow_dirty=args.allow_dirty) == metadata,
        "Source identity changed during build",
    )
    bundle = build / APPLICATION
    shutil.copyfile(identity_file, bundle / "RELEASE.json")
    suffix = ".zip" if sys.platform == "win32" else ".tar.gz"
    name = f"{PRODUCT}-v{version}-{metadata['platform']}-{metadata['machine']}"
    output = args.output_root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive, sidecar = output / (name + suffix), output / (name + ".sha256")
    require(not archive.exists() and not sidecar.exists(), "Existing package evidence preserved")
    create_archive(bundle, archive)
    require(archive_metadata(archive, APPLICATION) == metadata, "Archive source identity differs")
    with tempfile.TemporaryDirectory(prefix="mavlink-extracted-") as temporary:
        extracted = extract_archive(archive, Path(temporary) / "unpacked", APPLICATION)
        executable = extracted / (APPLICATION + (".exe" if sys.platform == "win32" else ""))
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/smoke_app.py"),
                str(executable),
                "--output",
                str(output / "acceptance"),
            ],
            cwd=temporary,
            check=True,
            timeout=100,
        )
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    sidecar.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(
        f"Extracted offline viewer passed: {archive.name} SHA-256 {digest}; source_dirty={metadata['source_dirty']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
