"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceFileSelector = void 0;
const React = require("react");
const ConfluenceFileSelector = ({ onCancel, onNext, onBrowseFiles, contextSuggestions, preloadedContent, preferredSpace, spaces = [], onSpaceChange, }) => {
    const mentioned = contextSuggestions?.mentioned_files ?? [];
    const related = contextSuggestions?.related_files ?? [];
    const projectTypeLabel = contextSuggestions?.project_type_label ?? '';
    const shouldSuggestReadme = contextSuggestions?.should_suggest_readme ?? false;
    const [selectedFiles, setSelectedFiles] = React.useState(() => {
        const initial = [...mentioned];
        if (initial.length === 0)
            return ['api.py', 'config.yaml', 'README.md', 'utils.py'];
        return initial;
    });
    const [availableFiles, setAvailableFiles] = React.useState(() => {
        const all = [...new Set([...mentioned, ...related, 'api.py', 'config.yaml', 'README.md', 'utils.py'])];
        return all.length > 0 ? all : ['api.py', 'config.yaml', 'README.md', 'utils.py'];
    });
    const [selectedSpace, setSelectedSpace] = React.useState(preferredSpace ?? 'DOCS');
    React.useEffect(() => {
        if (preferredSpace)
            setSelectedSpace(preferredSpace);
    }, [preferredSpace]);
    React.useEffect(() => {
        if (mentioned.length > 0 || related.length > 0) {
            setAvailableFiles(prev => [...new Set([...prev, ...mentioned, ...related])]);
            if (mentioned.length > 0) {
                setSelectedFiles(prev => [...new Set([...mentioned, ...prev])]);
            }
        }
    }, [mentioned.length, related.length]);
    const handleAddRelatedFiles = React.useCallback(() => {
        if (related.length === 0)
            return;
        setAvailableFiles(prev => [...new Set([...prev, ...related])]);
        setSelectedFiles(prev => [...new Set([...prev, ...related])]);
    }, [related]);
    const handleBrowseFiles = React.useCallback(async () => {
        if (onBrowseFiles) {
            const paths = await onBrowseFiles();
            if (paths?.length) {
                setAvailableFiles(prev => [...new Set([...prev, ...paths])]);
                setSelectedFiles(prev => [...new Set([...prev, ...paths])]);
            }
            return;
        }
        if (typeof window.acquireVsCodeApi === 'function') {
            window.acquireVsCodeApi().postMessage({ type: 'browseFiles' });
        }
    }, [onBrowseFiles]);
    React.useEffect(() => {
        if (typeof window.acquireVsCodeApi !== 'function' || onBrowseFiles)
            return;
        const handler = (e) => {
            if (e.data?.type === 'browseFilesResult' && Array.isArray(e.data.paths)) {
                setAvailableFiles(prev => [...new Set([...prev, ...e.data.paths])]);
                setSelectedFiles(prev => [...new Set([...prev, ...e.data.paths])]);
            }
        };
        window.addEventListener('message', handler);
        return () => window.removeEventListener('message', handler);
    }, [onBrowseFiles]);
    const toggleFile = (file) => {
        setSelectedFiles(prev => prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]);
    };
    const isCodeOnly = selectedFiles.length > 0 && selectedFiles.every(f => /\.(py|ts|tsx|js|jsx|java|go|rs|c|cpp|rb)$/i.test(f));
    const spaceOptions = spaces.length > 0 ? spaces : [{ key: selectedSpace, name: selectedSpace }];
    return (React.createElement("div", { className: "confluence-card", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px'
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, "Select files for intelligent formatting"),
        preferredSpace && (React.createElement("div", { style: { marginBottom: '8px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' } },
            "Previously used: ",
            React.createElement("strong", null, preferredSpace))),
        (spaces.length > 0 || onSpaceChange) && (React.createElement("div", { style: { marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' } },
            React.createElement("label", { style: { fontSize: '12px' } }, "Space:"),
            React.createElement("select", { value: selectedSpace, onChange: (e) => {
                    const k = e.target.value;
                    setSelectedSpace(k);
                    onSpaceChange?.(k);
                }, style: {
                    fontSize: '12px',
                    padding: '2px 6px',
                    backgroundColor: 'var(--vscode-input-background)',
                    color: 'var(--vscode-input-foreground)',
                    border: '1px solid var(--vscode-input-border)',
                    borderRadius: '2px',
                } }, spaceOptions.map(s => (React.createElement("option", { key: s.key, value: s.key }, s.name ?? s.key)))))),
        projectTypeLabel && (React.createElement("div", { style: {
                marginBottom: '8px',
                fontSize: '11px',
                padding: '4px 8px',
                backgroundColor: 'var(--vscode-badge-background)',
                color: 'var(--vscode-badge-foreground)',
                borderRadius: '2px',
                display: 'inline-block',
            } },
            "Intelligently detected: ",
            projectTypeLabel)),
        preloadedContent && (React.createElement("div", { style: { marginBottom: '8px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' } },
            "Selection pre-loaded (",
            preloadedContent.length,
            " chars)")),
        React.createElement("div", { style: { marginBottom: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' } },
            React.createElement("button", { type: "button", onClick: handleBrowseFiles, style: {
                    padding: '4px 8px',
                    backgroundColor: 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '12px',
                } }, "\uD83D\uDCC1 Browse Files..."),
            related.length > 0 && (React.createElement("button", { type: "button", onClick: handleAddRelatedFiles, style: {
                    padding: '4px 8px',
                    backgroundColor: 'var(--vscode-button-secondaryBackground)',
                    color: 'var(--vscode-button-secondaryForeground)',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '12px',
                } }, "Add related files"))),
        React.createElement("div", { style: { maxHeight: '150px', overflowY: 'auto', marginBottom: '12px', border: '1px solid var(--vscode-input-border)', padding: '4px' } }, availableFiles.map(file => (React.createElement("div", { key: file, style: { display: 'flex', alignItems: 'center', padding: '2px 0' } },
            React.createElement("input", { type: "checkbox", id: file, checked: selectedFiles.includes(file), onChange: () => toggleFile(file), style: { marginRight: '8px' } }),
            React.createElement("label", { htmlFor: file, style: { fontSize: '12px' } },
                file,
                mentioned.includes(file) && (React.createElement("span", { style: { marginLeft: '6px', fontSize: '10px', color: 'var(--vscode-descriptionForeground)' } }, "Based on your conversation"))))))),
        (isCodeOnly || shouldSuggestReadme) && (React.createElement("div", { style: { fontSize: '11px', marginBottom: '8px', color: 'var(--vscode-descriptionForeground)' } }, "Consider adding README or docs for context.")),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', color: 'var(--vscode-descriptionForeground)' } },
            "Selected: ",
            selectedFiles.length,
            " files",
            React.createElement("ul", { style: { margin: '4px 0 0 0', paddingLeft: '16px' } },
                React.createElement("li", null, "Automatically analyzed"),
                React.createElement("li", null, "Intelligently formatted"),
                React.createElement("li", null, "Perfectly organized"))),
        React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', gap: '8px' } },
            React.createElement("button", { type: "button", onClick: onCancel, style: {
                    padding: '4px 12px',
                    backgroundColor: 'transparent',
                    color: 'var(--vscode-button-foreground)',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: '2px',
                    cursor: 'pointer',
                } }, "Cancel"),
            React.createElement("button", { type: "button", onClick: () => onNext(selectedFiles), disabled: selectedFiles.length === 0, style: {
                    padding: '4px 12px',
                    backgroundColor: selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
                    opacity: selectedFiles.length === 0 ? 0.5 : 1,
                } }, "Next: Let AI Decide"))));
};
exports.ConfluenceFileSelector = ConfluenceFileSelector;
