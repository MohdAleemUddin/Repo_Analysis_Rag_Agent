import * as assert from "assert";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import { getTokenFilePath, readAgentToken } from "../../../vscode-extension/src/services/agentClient";

async function withTempDir(run: (dir: string) => Promise<void>) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "token-reader-"));
  try {
    await run(dir);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

describe("agentClient token reading", () => {
  const originalEnv = { ...process.env };

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("reads token using RAG_INDEX_DIR path", async () => {
    await withTempDir(async (tempDir) => {
      process.env.RAG_INDEX_DIR = tempDir;
      const tokenPath = getTokenFilePath();
      fs.mkdirSync(path.dirname(tokenPath), { recursive: true });
      fs.writeFileSync(tokenPath, "abc123", "utf8");

      const token = readAgentToken();
      assert.strictEqual(token, "abc123");
    });
  });

  it("falls back to USERPROFILE/.offline_rag_index", async () => {
    await withTempDir(async (tempDir) => {
      delete process.env.RAG_INDEX_DIR;
      process.env.USERPROFILE = tempDir;

      const tokenPath = getTokenFilePath();
      fs.mkdirSync(path.dirname(tokenPath), { recursive: true });
      fs.writeFileSync(tokenPath, "from_profile", "utf8");

      const token = readAgentToken();
      assert.strictEqual(token, "from_profile");
      assert.ok(tokenPath.startsWith(tempDir));
    });
  });
});
