const assert = require("assert");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const htmlModulePath = path.join(
  repoRoot,
  "vscode-extension",
  "src",
  "webview",
  "ui",
  "chatPanelHtml.ts"
);

const source = fs.readFileSync(htmlModulePath, "utf8");
const expectedPlaceholder = "Plan, @ for context, / for commands";

assert.ok(
  source.includes(expectedPlaceholder),
  "Placeholder text must match the exact required string."
);
