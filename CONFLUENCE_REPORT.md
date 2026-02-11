# Confluence – Detailed Report

## 1. Purpose and scope

The Confluence integration lets users:

- **Analyze** code/files (or chat context) and get an "intelligent" template suggestion.
- **Create** Confluence pages from that content (AI-formatted, with optional learning).
- **Document project** (US-16): scan workspace → analyze → pick project template → format → create one page.
- **Configure** Confluence (test connection, list spaces, validate config, defaults, preferred space per project).
- **Learn** from feedback and successful creations (template confidence, examples, embeddings).
- **Export/import** learned examples (US-6).
- **Track usage** for progressive disclosure (e.g. show "advanced" after N uses).

All of this is exposed as a **Confluence edge API** (FastAPI on port 8000) and used by the **VS Code extension** (chat panel, Confluence commands, file selector, intelligence dashboard).

---

## 2. Architecture

- **Backend (Python, port 8000)**  
  - **API:** Config + Confluence routes (one router; `register_confluence_routes` also calls `register_config_routes`).  
  - **Pipeline:** Coordinator runs a 4-agent pipeline: **Content analysis → Pattern matching → Formatting → Integration (Confluence REST).**  
  - **Data:** Optional PostgreSQL (pgvector) for templates, examples, creations, learning; file-based fallback when DB not configured.  
  - **Config:** Central config (env, DB URL, Confluence tuning), credential store (workspace-scoped), Pydantic schemas for validation.

- **Extension (TypeScript/React)**  
  - **Confluence API module:** Calls analyze, create, document-project, status, feedback, spaces, preferred-space, export/import with retries and no logging of auth/body.  
  - **Settings:** Confluence base URL, credentials (URL, email; token in SecretStorage), validation (e.g. Cloud = HTTPS).  
  - **UI:** Chat panel provider drives Confluence flows (save selection, document project, view creations, export/import), file selector, progress, results, intelligence dashboard, onboarding, space preferences.

- **Flow types**  
  - **Analyze only:** Files or content (or only `chat_context`) → content analysis + template match → return analysis + recommendation (and optional context_suggestions).  
  - **Create:** Analysis result (or inline params) + space/title → format → create page via Confluence REST → optional learning.  
  - **Document project:** Workspace path → scan → project analysis → project template match → format project content → create one page → learning.

---

## 3. Backend API (port 8000)

Base URL is the Confluence edge agent (e.g. `http://localhost:8000`). All Confluence endpoints are under `/confluence/...`.

### 3.1 Config (PRD §9.1)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/confluence/config/test-connection` | Validate credentials (url, email, api_token in body). Calls Confluence `/rest/api/user/current` (and optionally spaces). Returns `ok`, `latency_ms`, `spaces`, `error`. Never logs token. |
| POST | `/confluence/config/spaces` | Same credentials in body → list of `{key, name}` spaces. |
| POST | `/confluence/config/validate` | Pydantic validation of full/partial Confluence config; returns `valid` and optional `errors`. |
| GET | `/confluence/config/defaults` | Intelligent defaults (e.g. edition-based rate limit). Optional query `?url=...`. |
| GET | `/confluence/config/preferred-space` | Preferred space for project. Query `?project_path=...`. From DB (intelligent_creations) or default by project type (US-2). |

### 3.2 Confluence intelligence and creation

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/confluence/intelligent-analyze` | **Analyze** content. Body: `files` / `file_contents` / `content` and/or `chat_context`. If only `chat_context`: returns `context_suggestions` (mentioned/related files, project_type_label, etc.) and no analysis. Otherwise: memory check → `run_analyze(file_contents)` → returns `intelligence_analysis` + `intelligent_recommendation`; optional `context_suggestions` and `performance` (timings, targets_met, optimization_suggestions). PRD §9.2 error format on failure. |
| POST | `/confluence/intelligent-create` | **Create** page. Body: `base_url`, `space`/`space_key`, `auth`, `title`/suggested_title/title_override, `content`/`body_content` or `files`, `intelligence_context` (template_id, template_name, suggested_title, etc.), `feedback_for_learning`. Memory check → `run_create(...)` → returns page id/title/space/url; `performance`; optional `learning: true` when intelligence learned. |
| GET | `/confluence/intelligence-status` | **Status** (US-17). With request: uses DB metrics + `get_intelligence_status`. Without: last 20 in-memory records. Returns metrics, learning_progress, improvement_rates, last_operation_targets_met, team_examples_count. |
| POST | `/confluence/intelligence-feedback` | **Feedback.** Body: `creation_id`, `intelligence_score` (1–5), optional `feedback`. If score 1–5: `learn_from_feedback` (update template confidence, etc.) and return updated intelligence_metrics; else accept feedback and return status. |
| POST | `/confluence/document-project` | **Document project** (US-16). Body: `workspace_path`, `space`/`space_key`, `base_url`, `auth`. Requires non-empty workspace_path. Calls `run_document_project` (scan → analyze → template match → format → create). Returns confluence_url, intelligence_analysis, intelligent_recommendation, confidence, template_name, learning_indicator; plus performance. |
| POST | `/confluence/track-usage` | **Usage tracking** (US-11). Body: `userId`, `feature`, `workspace`. In-memory per (user, workspace). Returns `usageCount`, `showAdvanced` (e.g. after 2 uses), `learning`, `messages`. |

### 3.3 Export / import (US-6)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/confluence/examples/export` | Query: `project_path`, `from_date`, `to_date`, `template_type`. Returns JSON string of exported examples (from DB or file). |
| POST | `/confluence/examples/import` | Body: JSON (or string). Validates and imports; returns `message`, `imported_count` or error. |

### 3.4 Aliases

- `POST /confluence/intelligent-analyz` → same as intelligent-analyze (typo alias).  
- `GET /confluence/intelligent-analyz` → same as intelligence-status.

### 3.5 Health

- `GET /health` → `{"status": "ok", "service": "confluence-edge-agent"}`.

---

## 4. Backend pipeline (coordinator + agents)

**Coordinator** (`agents/coordinator.py`) runs a deterministic pipeline and keeps pipeline state (Idle → Analyzing → Matching → Formatting → Integrating → Completed/Failed) and last `CoordinatorError` for diagnosability.

### 4.1 Run analyze

- **Input:** `file_contents: list[str]`.  
- **Steps:**  
  1. **Analyzing:** For each file, `content_analysis_agent.analyze_file_with_timer(content)` → ContentProfile (content_types, languages, structure_signals, detected_patterns, ai_reasoning, etc.); memory check per file.  
  2. **Matching:** Combine profiles; derive `content_types_for_template` (code vs text); `pattern_matching_agent.match(combined, profiles[0], content_types_for_template, is_single_type)` → TemplateDecision (template_id, template_name, intelligence_score, confidence_breakdown, ai_reasoning).  
  3. **Completed:** Return `intelligence_analysis` (content_types, detected_patterns, intelligent_title, intelligence_confidence, ai_reasoning) and `intelligent_recommendation` (template_id, template_name, intelligence_reason, confidence_breakdown).

### 4.2 Run create

- **Input:** base_url, space_key, title, body_content, auth, feedback_for_learning, optional file_contents, optional template_decision_from_analyze.  
- **Steps:**  
  1. If file_contents: order (code first), merge into body_content.  
  2. **Analyzing:** Single content analysis (body).  
  3. **Matching:** Use template_decision_from_analyze if provided, else `match(body, profile)`.  
  4. **Formatting:** `formatting_agent.format_content(body, template_decision)` → Confluence storage HTML; validation/corrections (e.g. wrap in `<p>`, no script).  
  5. **Integrating:** `integration_agent.create_page(base_url, space_key, title, body_html, auth)` → Confluence REST create, then verify page (get_page); returns IntegrationResult (page id, url, title, space, verification).  
  6. If feedback_for_learning: `schedule_learning_after_create` (async).  
  7. Return API-shaped dict (id, title, space, url).

### 4.3 Run document project (US-16)

- **Input:** workspace_path, space_key, base_url, auth, optional progress_callback.  
- **Steps:**  
  1. **Analyzing:** `project_scanner.scan(workspace_path, limit=100)` → file paths (excludes .git, node_modules, venv, *.env, *.pem, credentials*, config/*.local*, etc. – NFR3).  
  2. `project_analyzer.analyze_project(paths)` → ProjectAnalysis (project_type: web app / API / library / database / testing / mixed, key_file_types, patterns, content_types, detected_patterns, source_file_count).  
  3. **Matching:** `project_template_matcher.match_project_template(analysis)` → ProjectTemplateMatch (template_name, template_id, confidence 0–100, match_count, ai_reasoning); fallback to "Mixed Project Intelligence Template" when confidence < 70%.  
  4. **Formatting:** Read first 30 files (up to 8KB each), merge; `format_project_content(project_analysis, template_name, template_match, merged)` → Confluence storage HTML.  
  5. **Integrating:** Create page with title like "{ProjectType} Project Documentation"; schedule learning.  
  6. Return confluence_url, intelligence_analysis, intelligent_recommendation, confidence, template_name, learning_indicator.

### 4.4 Agents (contracts and roles)

- **Content analysis agent:** Cache by content hash (optional), per-file timer, deterministic parsing (AST where applicable) + LangChain analysis_chain; outputs **ContentProfile** (content_types, languages, structure_signals, detected_patterns, relationships, confidence_scores, ai_reasoning).  
- **Pattern matching agent:** Uses **matching_chain** (vector + rules), timer <2s; outputs **TemplateDecision** (template_id, template_name, intelligence_score, ai_reasoning, confidence_breakdown). Fallback template when score < 0.3.  
- **Formatting agent:** **formatting_chain** → Confluence storage format; validation (script tags, root block); outputs **FormattedConfluencePayload** (confluence_storage_format, attachments, validation_results, ai_reasoning).  
- **Integration agent:** **confluence_tools** (create_page, get_page); retries and 429 handling; post-create verification; outputs **IntegrationResult** (page, verification, retries_used, rate_limit_state).  
- **Learning agent:** `on_creation_success` (store_example, update_embeddings, record_learning); `learn_from_feedback` (apply_feedback, update template confidence, record_learning); uses example_manager and DB adapters.

---

## 5. Confluence client and tools

- **confluence/client.py:** Single `requests.Session`; `create_page` (POST /rest/api/content) with retries (1s, 2s, 4s) and 429 → wait 30s; HTTPS enforced for base_url; token validation when auth provided.  
- **langchain/tools/confluence_tools.py:** Wraps client `create_page` and `get_page`; used by integration_agent for create and verify.

---

## 6. Config and validation

- **config/config.py:** Database URL (CONFLUENCE_DATABASE_URL / DATABASE_URL), pool settings, Confluence tuning from env (rate_limit, burst_limit, retry_attempts, learning_enabled, team_sharing_opt_in). Workspace-scoped credentials from auth credential_store. NFR1 constants: ANALYSIS_MAX_SECONDS_PER_FILE=3, TEMPLATE_SELECTION_MAX_SECONDS=2, CREATE_E2E_MAX_SECONDS=15, CONFLUENCE_MEMORY_LIMIT_MB=300. Cache and chunk settings for analysis.  
- **config/confluence_config.py:** detect_edition (cloud vs server), get_intelligent_defaults, test_connection (user/current + spaces), get_available_spaces, get_default_space_for_project_type (e.g. src/app → DEV, docs → DOCS), get_preferred_space (DB then default).  
- **config/confluence_schema.py:** ConfluenceCredentials (url HTTPS for Cloud, email, api_token), path length/traversal limits, ConfluenceConfigValidate; validators never log token.

---

## 7. Error handling and monitoring

- **error_handler.py:** Classifies exceptions (network, auth, rate_limit, content, intelligence_error, resource_limit). PRD §9.2 response: error, message, intelligence_suggestion, fallback_available, intelligence_confidence, actions, category, suggested_files. record_success / record_failure for reliability metrics.  
- **prd_monitor.py:** PerformanceRecord (operation_id, per_file_analysis_ms, template_selection_ms, create_e2e_ms, peak_memory_mb, targets_met). Timers: timer_per_file_analysis, timer_template_selection, timer_create_e2e. check_memory_before_step (CONFLUENCE_MEMORY_LIMIT_MB). start_operation / get_operation_record / append_record; verify_targets_met.  
- **Optimizer:** get_optimization_suggestions when targets not met.

---

## 8. Context analyzer (chat context, US-2)

- **context_analyzer.py:** Optional input: last N messages, selected_text, workspace_path. Extracts file paths (regex), functions, modules; resolves related files (same dir); infers project type label (python_fastapi, react, docs, mixed, etc.) and suggests README. No Chroma; used only for context_suggestions when analyze is called with chat_context only or when analysis fails.

---

## 9. Database and data (PRD §8.1, migrations)

- **Migrations (e.g. 004_confluence_tables.sql):**  
  - **intelligent_templates:** id, name, description, content_type, language, template_content, is_intelligent, source_examples, intelligence_score, success_rate, confidence_avg, intelligence_embedding (vector 1536), timestamps.  
  - **intelligence_examples:** id, content_profile (JSONB), template_used (FK), created_page_url, intelligence_metrics, learned_at, intelligence_embedding, confidence_score, user_feedback, improvement_suggestions.  
  - **intelligent_creations:** id, user_id, project_path, files_included, content_intelligence, selected_template, intelligence_confidence, confluence_page_id, confluence_url, created_at, intelligence_score, user_satisfaction, auto_improvement_applied.  
  - **intelligence_learning:** id, learning_type, before_score, after_score, improvement, learned_from (FK), learned_at, etc.  
  - Seed: 7 intelligent templates, 50+ intelligence_examples (content_profile + template_used).  

- **db_adapter.py:** get_connection (CONFLUENCE_DATABASE_URL); db_execute; db_fetch_examples (with filters); db_fetch_examples_count; db_fetch_intelligence_metrics; db_ensure_creation_for_feedback; db_get_creation_template_id; db_update_template_confidence; db_get_preferred_space (for project_path). When DB not configured, callers use file-based examples/status.

---

## 10. VS Code extension – Confluence

### 10.1 Commands

- **confluence.saveToIntelligent** (Ctrl+Shift+C / Cmd+Shift+C): Open chat panel and trigger Confluence save (intelligent flow).  
- **confluence.saveSelection:** Store current selection in globalState, open panel, trigger Confluence save.  
- **confluence.documentProject:** Open panel, trigger document project (requires workspace folder).  
- **confluence.viewCreations:** Open panel, trigger view creations.  
- **confluence.exportExamples / importExamples:** Open panel, trigger export/import.  
- **confluence.configureSettings / configureProjectSettings:** Open Confluence settings.  
- **confluence.testConnection:** Validate URL/email/token via POST `/confluence/config/test-connection`; show result and cache spaces.  
- **confluence.storeApiToken:** Prompt for token, store in SecretStorage.  
- Editor context menu: "Save Selection (AI Formatting)" when there is selection.

### 10.2 Confluence API client (confluence-api.ts)

- **Config:** baseUrl (edge agent, e.g. 8000), confluenceInstanceUrl (Confluence instance for create), auth [email, token].  
- **Health:** checkBackendHealth before analyze/create.  
- **Retry:** postJsonWithRetry: 3 retries, exponential backoff; 429 → wait 30s; 401/403/404 non-retryable; network errors retried. No logging of request body or auth (US-14).  
- **Calls:** intelligentAnalyze, intelligentCreate, getIntelligenceStatus, postIntelligenceFeedback, documentProject, getPreferredSpace, fetchSpaces, exportExamples, importExamples.

### 10.3 Settings (confluence-settings.ts)

- **confluence.apiBaseUrl:** Edge agent URL (default http://localhost:8000).  
- **confluence.credentials.url / .email:** Confluence instance and email.  
- Token: SecretStorage key `confluence.apiToken` (getStoredToken / setStoredToken).  
- validateConfluenceUrl: Cloud URLs must be HTTPS.  
- getConfluenceConfigAsync: builds ConfluenceApiConfig from workspace config + SecretStorage.

### 10.4 Types (types.ts)

- AnalyzeResponse, IntelligenceAnalysis, IntelligentRecommendation; IntelligenceErrorResponse (PRD §9.2); IntelligenceSummary, IntelligentPage, CreateResponse; ProgressUpdate; IntelligenceStatusResponse, IntelligenceMetrics; etc.

### 10.5 Chat panel Confluence flow

- **ChatPanelViewProvider** holds confluenceState (analyzeResult, fileContents, selectedPaths, lastTitle, lastSpace, contextSuggestions).  
- **triggerConfluenceSave:** Handle Confluence save with context (files or preloaded selection).  
- **triggerDocumentProject:** Resolve workspace root, send document-project request with space/base_url/auth.  
- **triggerViewCreations / triggerExportExamples / triggerImportExamples:** Switch UI to the corresponding view.  
- Uses **getConfluenceConfigAsync**, **intelligentAnalyze**, **intelligentCreate**, **documentProject**, **getPreferredSpace**, **fetchSpaces**, **getIntelligenceStatus**, **postIntelligenceFeedback**, **exportExamples**, **importExamples**, **trackConfluenceUsage**.  
- File selector, analysis view, progress, results, intelligence dashboard, onboarding, space preferences, error messages (simple-language), badges (AI-formatted, confidence, learning) live in `confluence/` TS/TSX and webview UI.

---

## 11. Configuration surface (extension)

From package.json and settings, Confluence exposes many options, including:

- **confluence.apiBaseUrl**, **rag.agentBaseUrl**  
- **confluence.credentials.url**, **confluence.credentials.email** (token via command)  
- **confluence.defaults.spaceMapping** (default space per project type)  
- **confluence.performance:** rateLimit, burstLimit, retryAttempts, timeouts (analysis, templateSelection, pageCreation, connection), cache (enabled, ttl, maxSize)  
- **confluence.logging:** level, includeSensitive, maxFileSize  
- **confluence.learning:** enabled, retentionDays, minConfidence, autoImprove  
- **confluence.advanced:** exportPath, importPath, autoExport  
- **confluence.templates.overrides:** disabledTemplates, priorityOrder, customTemplatesPath  
- **confluence.intelligence:** confidenceThreshold, autoTitle, autoSpace, explainDecisions  
- **confluence.risks:** allowOverrides, showConfidence, fallbackTemplates, maxFileSize  
- **confluence.mode.intelligent:** default intelligent vs manual

---

## 12. Summary table

| Layer | Components |
|-------|------------|
| **API** | Config (test-connection, spaces, validate, defaults, preferred-space); intelligent-analyze, intelligent-create, document-project, intelligence-status, intelligence-feedback, track-usage; examples export/import. |
| **Pipeline** | Coordinator (analyze → match → format → integrate); content_analysis, pattern_matching, formatting, integration, learning agents; project_scan, project_analyzer, project_template_matcher for US-16. |
| **Confluence** | client (session, create_page, retries, 429); confluence_tools (create_page, get_page). |
| **Config** | config.py (DB, NFR1 limits, tuning); confluence_config (test_connection, spaces, preferred_space); confluence_schema (credentials, validate). |
| **Data** | PostgreSQL: intelligent_templates, intelligence_examples, intelligent_creations, intelligence_learning; db_adapter; file fallback; status_manager, example_manager. |
| **Errors & NFR** | error_handler (PRD §9.2, classification); prd_monitor (timers, memory, PerformanceRecord). |
| **Extension** | Commands (save, document project, view/export/import, settings, test connection, store token); confluence-api (retry, no auth log); confluence-settings (SecretStorage, URL validation); types; ChatPanelViewProvider Confluence state and triggers; file selector, dashboard, onboarding, badges. |
