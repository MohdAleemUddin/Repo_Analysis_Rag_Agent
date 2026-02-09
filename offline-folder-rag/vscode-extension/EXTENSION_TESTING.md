# Extension testing – simple steps

## 1. Build the extension

```bash
cd offline-folder-rag/vscode-extension
npm install
npm run compile
```

## 2. Run unit tests (if any)

```bash
npm test
```

## 3. Launch the extension in a Development Host (recommended)

1. Open this repo in VS Code (or Cursor).
2. Open the `vscode-extension` folder (or the repo root).
3. Press **F5** or use **Run > Start Debugging**.
4. A new window opens with the extension loaded (“Extension Development Host”).
5. In that window:
   - Open a folder (e.g. a project with some code).
   - **Command Palette** (Ctrl+Shift+P / Cmd+Shift+P) → run **“PRD: Save to Confluence (Intelligent)”** or **“🤖 Save to Confluence (AI will format perfectly)”**.
   - Or right‑click in the editor (with some text selected) → **“🤖 Save to Confluence (AI will format perfectly)”** (chat flow, no panel).
   - Use **“Confluence: Configure Project Settings”** to open the config panel and test connection.

## 4. Package and install for a manual test (optional)

```bash
npm install -g @vscode/vsce
vsce package
```

Then install the generated `.vsix` in VS Code: **Extensions** → **...** → **Install from VSIX** → choose the file.

## 5. Quick checklist

- [ ] Extension Development Host launches (F5).
- [ ] Command **“PRD: Save to Confluence (Intelligent)”** opens the file selector (or expected UI).
- [ ] Right‑click **“🤖 Save to Confluence”** runs without opening a new panel and shows the info message.
- [ ] **“Confluence: Configure Project Settings”** opens the config panel; Test connection works if the edge agent is running and credentials are set.
