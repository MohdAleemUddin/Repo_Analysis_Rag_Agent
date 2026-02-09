const fs = require("fs");
const path = require("path");
const endpoint = "http://127.0.0.1:7247/ingest/f4ddbb8f-ad83-4079-ab0c-6eca658a07b5";

const log = (payload) => {
    fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    }).catch(() => {});
};

const run = async () => {
    const targetDirArg = process.argv[2];
    const runId = process.argv[3] || "initial";
    const targetDir = targetDirArg
        ? path.resolve(process.cwd(), targetDirArg)
        : __dirname;

    try {
        process.chdir(targetDir);
    } catch (error) {
        // #region agent log
        log({
            sessionId: "debug-session",
            runId,
            hypothesisId: "H0",
            location: "scripts/checkModule.js:26",
            message: "Failed to switch working directory",
            data: { error: error.message, targetDir },
            timestamp: Date.now(),
        });
        // #endregion
    }

    const basePayload = {
        sessionId: "debug-session",
        runId,
        timestamp: Date.now(),
        contextDir: targetDir,
    };
    const resolverOptions = { paths: [targetDir] };

    // #region agent log
    log({
        ...basePayload,
        hypothesisId: "H1",
        location: "scripts/checkModule.js:33",
        message: "Checking node_modules directory",
        data: {
            nodeModulesExists: fs.existsSync("node_modules"),
            targetDir: basePayload.contextDir,
        },
    });
    // #endregion

    try {
        require.resolve("vscode", resolverOptions);
        // #region agent log
        log({
            ...basePayload,
            hypothesisId: "H2",
            location: "scripts/checkModule.js:41",
            message: "Resolved vscode module",
            data: { resolved: true, targetDir: basePayload.contextDir },
        });
        // #endregion
    } catch (error) {
        // #region agent log
        log({
            ...basePayload,
            hypothesisId: "H2",
            location: "scripts/checkModule.js:48",
            message: "Failed to resolve vscode module",
            data: { error: error.message, targetDir: basePayload.contextDir },
        });
        // #endregion
    }

    try {
        require.resolve("@types/vscode", resolverOptions);
        // #region agent log
        log({
            ...basePayload,
            hypothesisId: "H3",
            location: "scripts/checkModule.js:56",
            message: "Resolved @types/vscode",
            data: { resolved: true, targetDir: basePayload.contextDir },
        });
        // #endregion
    } catch (error) {
        // #region agent log
        log({
            ...basePayload,
            hypothesisId: "H3",
            location: "scripts/checkModule.js:63",
            message: "Failed to resolve @types/vscode",
            data: { error: error.message, targetDir: basePayload.contextDir },
        });
        // #endregion
    }
};

run();
