/** Jason Stys: TypeScript compiler declaration/parameter index for authored sources. Map: docs/SOURCE_MAP.md. */
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

/** Recursively collect only the explicitly selected authored source directories in stable lexical order. */
function collect(root) {
  return fs
    .readdirSync(root, { withFileTypes: true })
    .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0))
    .flatMap((entry) => {
      const file = path.join(root, entry.name);
      return entry.isDirectory()
        ? collect(file)
        : /\.(?:ts|mjs)$/.test(file)
          ? [file]
          : [];
    });
}
for (const file of [
  ...collect("ui/src"),
  ...collect("tests/browser"),
  "tools/source_index.mjs",
  "vite.config.ts",
  "playwright.config.ts",
]) {
  const source = ts.createSourceFile(
    file,
    fs.readFileSync(file, "utf8"),
    ts.ScriptTarget.Latest,
    true,
  );
  const records = new Map();
  /** Visit declarations without evaluating source or trying to infer a call graph. */
  function visit(node) {
    if (
      (ts.isVariableDeclaration(node) ||
        ts.isFunctionDeclaration(node) ||
        ts.isClassDeclaration(node) ||
        ts.isParameter(node) ||
        ts.isTypeAliasDeclaration(node)) &&
      node.name
    ) {
      const name = node.name
        .getText(source)
        .replace(/\s+/g, " ")
        .replaceAll("|", "/");
      const line =
        source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
      records.set(
        `${line}:${name}`,
        `| \`${file.replaceAll("\\", "/")}\` | ${line} | \`${name}\` |`,
      );
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  for (const row of records.values()) console.log(row);
}
