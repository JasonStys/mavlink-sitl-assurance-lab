"""Jason Stys: deterministic file catalog and Python/C++/TypeScript AST declaration map.

Functions/variables/lines: docs/SOURCE_MAP.md. Tree-sitter provides C++ syntax anchors,
not compiler type resolution, reachability, call graphs or unused-code analysis.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import tree_sitter_cpp
from tree_sitter import Language, Parser

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".runtime",
    ".venv",
    "node_modules",
    "dist",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "test-results",
    "playwright-report",
}
DESCRIPTIONS = {
    ".gitignore": "Keep private/local runtime data, secrets, dependencies and build output outside Git.",
    ".gitattributes": "Normalize tracked source line endings across operating systems.",
    ".prettierignore": "Keep generated canonical schema and fixture formatting under its generator.",
    "README.md": "Purpose, quick start, supported native matrix, verification and major file/feature summary.",
    "LICENSE": "MIT license for original code; upstream PX4/MAVSDK keep their independent licenses.",
    "SECURITY.md": "Private security reporting and explicit non-operational threat boundaries.",
    "CONTRIBUTING.md": "Contributor workflow, style, independent review and unchanged acceptance gates.",
    "package.json": "Exact frontend tools and local build, viewer, test, formatting and audit commands.",
    "package-lock.json": "Resolved npm dependency versions and integrity hashes.",
    "pyproject.toml": "Python support, Ruff rules, pytest configuration and explicit coverage denominator.",
    "requirements.in": "Pinned Python report, test, style, audit and source-index grammar inputs.",
    "requirements.lock": "Hash-locked Python core/test/source-index dependency graph.",
    "requirements-native.in": "Native SDK and pinned upstream PX4 build-tool inputs.",
    "requirements-native.lock": "Hash-locked native SDK, build and integration dependency graph.",
    "tsconfig.json": "Strict TypeScript checking without unused declarations or output emission.",
    "ui/schema/report.schema.json": "Generated canonical serialization contract consumed by the CSP-safe viewer.",
    "examples/synthetic.json": "Deterministic, explicitly synthetic report; never native acceptance evidence.",
    "docs/ARCHITECTURE.md": "Requirements, data flow, accepted design decisions, costs and complexity bounds.",
    "docs/OPERATIONS.md": "Native setup, report recovery, viewer use, failure triage, teardown and rollback.",
    "docs/SECURITY.md": "Threat model, fixed-port ownership, untrusted evidence handling and remaining gaps.",
    "docs/TESTING.md": "Risk-based strategy, independent oracles, coverage boundaries and known gaps.",
    "docs/VALIDATION.md": "Observed results, failed-attempt history and verified CI/source evidence links.",
    "docs/RESEARCH.md": "Primary references and version-specific integration findings.",
    "docs/FILE_CATALOG.md": "Generated specific responsibility summary for every authored deliverable.",
    "docs/SOURCE_MAP.md": "Generated physical declaration/parameter/assigned-variable navigation.",
    "docs/NATIVE_RESULTS.json": "Source-linked measured native acceptance summary, not a synthetic fixture.",
}


def files():
    """Prune ignored trees before traversing; emit stable POSIX-relative ordering on every OS."""
    result = []
    for directory, directories, names in os.walk(ROOT):
        directories[:] = [name for name in directories if name not in EXCLUDED]
        result.extend(Path(directory) / name for name in names if not name.startswith(".coverage"))
    return sorted(
        (path for path in result if path.is_file()),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def cpp_symbols(content):
    """Index C++ declarations using syntax nodes, not regex matches that could mistake comments for code."""
    tree = Parser(Language(tree_sitter_cpp.language())).parse(content.encode("utf-8"))
    pending = [tree.root_node]
    result = set()
    while pending:
        node = pending.pop()
        if node.type in {
            "function_declarator",
            "class_specifier",
            "struct_specifier",
            "enum_specifier",
            "init_declarator",
            "parameter_declaration",
            "field_declaration",
        }:
            declaration = node.child_by_field_name("declarator") or node.child_by_field_name("name")
            if declaration:
                text = " ".join(declaration.text.decode("utf-8").split()).replace("|", "/")
                result.add((declaration.start_point.row + 1, text))
        pending.extend(node.named_children)
    return sorted(result)


def render():
    """Generate specific file responsibilities and physical syntax anchors without executing source."""
    catalog = [
        "# File catalog",
        "",
        "By Jason Stys. Generated by `python tools/docs_index.py`.",
        "",
        "| File | Responsibility |",
        "| --- | --- |",
    ]
    source_map = [
        "# Source declaration map",
        "",
        "By Jason Stys. Generated from Python/TypeScript AST and C++ tree-sitter syntax.",
        "Parameters are on declaration lines; local/assigned names have their own anchors. These are navigation, not semantic/call-graph proofs.",
        "File/function/class headers describe responsibilities. Generated schemas/fixtures and CSS use the file catalog.",
        "",
        "| File | Line | Declaration / variable |",
        "| --- | ---: | --- |",
    ]
    for path in files():
        relative = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        description = DESCRIPTIONS.get(relative) or next(
            (
                line.strip(' #/*!-"<>')
                for line in content.splitlines()[:12]
                if "Jason Stys:" in line
            ),
            None,
        )
        if description is None:
            raise ValueError(f"Add a meaningful file responsibility: {relative}")
        catalog.append(f"| `{relative}` | {description.replace('|', '/')} |")
        records = set()
        if path.suffix == ".py":
            for node in ast.walk(ast.parse(content)):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = "class"
                    if not isinstance(node, ast.ClassDef):
                        params = ", ".join(
                            arg.arg
                            for arg in [
                                *node.args.posonlyargs,
                                *node.args.args,
                                *node.args.kwonlyargs,
                            ]
                        )
                        if node.args.vararg:
                            params += f", *{node.args.vararg.arg}"
                        if node.args.kwarg:
                            params += f", **{node.args.kwarg.arg}"
                    records.add((node.lineno, f"{node.name}({params})"))
                elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(
                    node.ctx, ast.Store
                ):
                    records.add((node.lineno, ast.unparse(node).replace("|", "/")))
        elif path.suffix in (".cpp", ".hpp"):
            records.update(cpp_symbols(content))
        source_map.extend(f"| `{relative}` | {line} | `{name}` |" for line, name in sorted(records))
    binary = shutil.which("node")
    if binary is None:
        raise RuntimeError("Node.js required for TypeScript declaration indexing")
    source_map.extend(
        subprocess.check_output([binary, "tools/source_index.mjs"], cwd=ROOT, text=True, timeout=30)
        .strip()
        .splitlines()
    )
    return {
        "docs/FILE_CATALOG.md": "\n".join(catalog) + "\n",
        "docs/SOURCE_MAP.md": "\n".join(source_map) + "\n",
    }


def main():
    """Create deterministic navigation, or fail CI when tracked indexes are stale."""
    for name, content in render().items():
        target = ROOT / name
        if "--check" in sys.argv:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale {name}; run python tools/docs_index.py")
        else:
            target.parent.mkdir(exist_ok=True)
            target.write_text(content, encoding="utf-8")
    print(f"File/source navigation verified for {len(files())} files")


if __name__ == "__main__":
    main()
