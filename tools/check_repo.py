"""Jason Stys: source/header/workflow and bounded production-output contracts.

Functions/variables/lines: docs/SOURCE_MAP.md. Narrow secret patterns are a guard,
not complete secret detection, a security certification or behavioral acceptance.
"""

import gzip
import re
import sys
from pathlib import Path

from docs_index import ROOT, files


def main():
    """Require documented public-safe deliverables, pinned Actions and unchanged bundle budgets."""
    for name in (
        "README.md",
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY.md",
        "docs/OPERATIONS.md",
        "docs/TESTING.md",
        "docs/VALIDATION.md",
        "docs/RESEARCH.md",
        "docs/FILE_CATALOG.md",
        "docs/SOURCE_MAP.md",
    ):
        assert (ROOT / name).is_file(), name
    for path in files():
        content = path.read_text(encoding="utf-8")
        assert not re.search(
            r"(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
            content,
        ), path
        if path.suffix in {".py", ".ts", ".mjs", ".cpp", ".hpp", ".css", ".html"}:
            header = "\n".join(content.splitlines()[:12])
            assert "Jason Stys:" in header and "SOURCE_MAP.md" in header, path
        if path.parent.name == "workflows":
            for action in re.findall(r"uses:\s*([^\s]+)", content):
                assert re.fullmatch(r"[\w./-]+@[a-f0-9]{40}", action), action
            assert "upload-artifact@" not in content and "actions/cache@" not in content
    if "--dist" in sys.argv:
        scripts = list(Path("dist/assets").glob("*.js"))
        styles = list(Path("dist/assets").glob("*.css"))
        assert scripts and styles and Path("dist/index.html").is_file(), "Build output missing"
        js = sum(len(gzip.compress(path.read_bytes())) for path in scripts)
        css = sum(len(gzip.compress(path.read_bytes())) for path in styles)
        assert js <= 50000 and css <= 8000, (js, css)
        print(f"Production gzip: JS {js} / 50000 B, CSS {css} / 8000 B")
    print(
        "Public source, authored headers, documentation, pinned workflows and output contracts passed"
    )


if __name__ == "__main__":
    main()
