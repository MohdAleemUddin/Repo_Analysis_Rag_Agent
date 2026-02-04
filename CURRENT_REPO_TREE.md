# Repository Tree Structure - Repo Analysis RAG Agent

**Generated:** February 3, 2026  
**Repository:** repo_analysis_rag1_final/repo_analysis_rag1  
**Branch:** Confluence-agents

## Directory Structure

```
repo_analysis_rag1/
├── .cursor/
│   └── plans/
│       ├── chromadb-stub-7c5b9d49.plan.md
│       └── confluence-integration.plan.md
├── .cursorindexingignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .specstory/
│   ├── .gitignore
│   ├── .project.json
│   ├── .what-is-this.md
│   └── history/
│       ├── 2026-02-03_07-41Z-repo-analysis-rag-agent-push.md
│       ├── 2026-02-03_08-02Z-repository-snapshot-and-markdown-file.md
│       ├── 2026-02-03_09-35Z-new-project-repository-structure.md
│       ├── 2026-02-03_10-37Z-venv-folder-update.md
│       ├── 2026-02-03_12-07Z-chat-only-confluence-integration-user-story.md
│       ├── 2026-02-03_13-39Z-vs-code-extension-activation-and-dev-host.md
│       ├── 2026-02-03_14-19Z-file-picker-and-selector-ui-issues.md
│       ├── 2026-02-03_14-47Z-confluence-browse-files-button-fix.md
│       └── 2026-02-03_18-17Z-repository-tree-snapshot.md
├── .vscode/
│   ├── launch.json
│   └── tasks.json
├── alembic/
│   └── versions/
│       └── README.md
├── alembic.ini
├── confluence_data/
│   ├── config/
│   │   ├── default_config.json
│   │   ├── rate_limits.json
│   │   └── spaces_config.json
│   ├── examples/
│   │   ├── export_format.json
│   │   └── successful_creations/
│   │       └── example_001.json
│   └── templates/
│       ├── config_template.json
│       ├── database_template.json
│       ├── library_template.json
│       ├── mixed_project_template.json
│       ├── python_api_template.json
│       ├── testing_template.json
│       └── web_app_template.json
├── confluence_requirements.txt
├── docker/
│   ├── Dockerfile.confluence
│   └── Dockerfile.mcp
├── docker-compose.test.yml
├── docker-compose.yml
├── migrations/
│   ├── 002_confluence_tables.sql
│   ├── 003_intelligence_extension.sql
│   └── 004_confluence_tables.sql
├── offline-folder-rag/  <-- PRIMARY IMPLEMENTATION
│   ├── edge_agent/
│   │   ├── __init__.py
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── agents/
│   │       │   └── [7 Python files]
│   │       ├── api/
│   │       │   └── [4 Python files]
│   │       ├── config/
│   │       │   └── [4 Python files]
│   │       ├── confluence/
│   │       │   └── [16 Python files]
│   │       ├── indexing/
│   │       │   └── [1 Markdown file]
│   │       ├── langchain/
│   │       │   └── [8 Python files]
│   │       ├── logging/
│   │       │   └── [3 Python files]
│   │       ├── mcp_server/
│   │       │   └── [6 Python files]
│   │       ├── retrieval/
│   │       │   └── [1 Markdown file]
│   │       ├── security/
│   │       │   └── [1 Markdown file]
│   │       └── tools/
│   │           ├── __init__.py
│   │           ├── doctor.py
│   │           └── search.py
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── backup_confluence_data.py
│   │   ├── log_cleanup.py
│   │   └── setup_confluence.py
│   ├── unittests/
│   │   ├── functionaltestcases/
│   │   │   └── [1 Markdown file]
│   │   └── unittest_cases/
│   │       └── confluence_unittests/
│   │           └── [1 Python file]
│   └── vscode-extension/
│       ├── .cursorindexingignore
│       ├── .specstory/
│       │   └── [1 file]
│       ├── out/
│       │   └── confluence/
│       │       └── [13 JavaScript files]
│       ├── package-lock.json
│       ├── package.json
│       ├── src/
│       │   ├── confluence/
│       │   │   └── [12 TypeScript files, 3 TypeScript config files, 1 JSON file]
│       │   └── extension.ts
│       ├── tests/
│       │   └── confluence/
│       │       └── test_confluence_import.ts
│       └── tsconfig.json
├── pytest.ini
├── repo_analysis_rag/
│   ├── .cursorindexingignore
│   ├── .specstory/
│   │   └── history/
│   │       └── [Multiple SpecStory history files]
│   └── Zeroui_Repo_Analysis_Rag_Agent/
│       ├── .cursor/
│       ├── .git/
│       ├── .specstory/
│       ├── .vscode/
│       └── offline-folder-rag/  <-- NESTED DUPLICATE
│           ├── edge_agent/
│           ├── scripts/
│           ├── testcases/
│           ├── tests/
│           ├── unittests/
│           └── vscode-extension/
│               ├── app/
│               ├── functionaltestcases/
│               ├── unittest_cases/
│               ├── src/
│               └── tests/
├── requirements.txt
├── run-local-cicd.ps1
├── test-results-integration.xml
├── test-results-unit.xml
└── tests/
    ├── confluence/
    │   ├── __init__.py
    │   ├── test_api_prd_format.py
    │   ├── test_api_router.py
    │   ├── test_client_auth.py
    │   ├── test_e2e_workflows.py
    │   ├── test_imports.py
    │   ├── test_intelligence_learning.py
    │   ├── test_page_tracker.py
    │   ├── test_performance_targets.py
    │   ├── test_prd_compliance.py
    │   ├── test_reliability.py
    │   ├── test_security_compliance.py
    │   ├── test_state_machine.py
    │   ├── test_templates.py
    │   └── test_prd_compliance.py
    └── edge_agent/
        ├── integration/
        │   └── README.md
        └── unit/
            └── README.md
```

## Key Components

### Core Modules
- **repo_analysis_rag/** - Main repository analysis RAG implementation (183 files)
- **offline-folder-rag/** - Primary offline folder RAG processing system (Root level)
- **Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/** - Nested duplicate/legacy offline RAG implementation
- **confluence_data/** - Confluence integration data and templates

### Development Tools
- **.cursor/** - Cursor IDE plans and configurations
- **.vscode/** - VS Code workspace settings
- **.github/** - GitHub Actions workflows

### Testing & Quality
- **tests/** - Comprehensive test suite for confluence and edge agent
- **pytest.ini** - Pytest configuration
- **alembic/** - Database migration management

### Infrastructure
- **docker/** - Containerization files
- **docker-compose.yml** - Multi-service orchestration
- **migrations/** - Database schema migrations

## Notes
- Repository excludes common development artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`)
- Contains both Python backend services and TypeScript/React VS Code extension
- Includes comprehensive Confluence integration capabilities
- Supports both online and offline RAG processing modes
- **Warning:** There are two `offline-folder-rag` directories. The root-level one is the primary implementation, while the nested one inside `Zeroui_Repo_Analysis_Rag_Agent` appears to be a duplicate or legacy version.