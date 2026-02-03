GROUP 1: SINGLE INTERFACE INTEGRATION
User Story 1: Chat-Only Confluence Integration
Goal: As a RAG user, I want to save files to Confluence entirely within the existing RAG chat interface so I never need to open new tabs or panels.

Acceptance Criteria:

Single Interface Compliance:

"💾 Save to Confluence" button added to existing RAG chat input area exactly as shown in PRD

Button appears exactly where send button is (right side of input) with 💾 icon

All Confluence interactions happen via chat messages (no modals, no new tabs)

File selection appears as interactive chat message

Analysis results appear as chat message with exact fields

Progress updates appear as single updating chat message

Success/failure appears as chat message exactly as PRD design

Maximum 3-Click Flow:

Click 1: "💾 Save to Confluence" button

Click 2: Select files in file selector (appears in chat)

Click 3: "Create Perfect Page" button after seeing intelligent analysis

No intermediate decisions: system auto-selects template, title, space

Title is editable only via "Edit Title" button as shown in PRD

No New UI Elements:

No separate Confluence panel in VS Code sidebar

No new tabs or views in VS Code

No modal dialogs that block chat

All UI components render as chat messages

Command palette commands open chat interface, not separate windows

Performance Targets:

File selector loads in <2 seconds

File selection interaction feels instant

No perceptible lag in chat interface

Memory usage ≤300MB during Confluence operations

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceButton.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceProgress.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceResults.tsx
- offline-folder-rag/vscode-extension/src/confluence/types.ts

MODIFY:
- offline-folder-rag/vscode-extension/src/extension.ts (add button integration)
- offline-folder-rag/vscode-extension/package.json (add UI contributions)

NO CHANGES:
- offline-folder-rag/vscode-extension/src/ (existing UI structure)
User Story 2: Context-Aware File Suggestions
Goal: As a user discussing code in RAG chat, I want the system to intelligently suggest related files for Confluence documentation based on chat context and remember my space preferences.

Acceptance Criteria:

Chat Context Analysis:

Analyze last 5 chat messages for mentioned files/functions

Detect project context from active workspace

Identify related files (imports, includes, same module)

Prioritize files mentioned in recent chat conversations

When right-clicking on selected text, pre-load that content for Confluence

Intelligent File Suggestions:

When clicking "Save to Confluence", pre-select files mentioned in chat with "Based on your conversation" badge

Provide "Add related files" button to include imports/dependencies

Suggest README/docs if code files selected

Show "Intelligently detected: Python FastAPI code" badge

Space Preference Memory:

Remember user's preferred Confluence space PER PROJECT FOLDER

Auto-select space based on project type: DEV for code, DOCS for docs

Show "Previously used: DEV" indicator

Allow one-click space change via dropdown

Performance:

Context analysis completes in <1 second

File suggestions appear instantly in file selector

No impact on existing RAG chat performance

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/context_analyzer.py
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceContextMenu.tsx

MODIFY:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx (add context suggestions)
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (add context parameter)
- offline-folder-rag/edge_agent/app/config/confluence_config.py (add space preferences)

NO CHANGES:
- offline-folder-rag/edge_agent/app/indexing/ (Existing RAG indexing)
GROUP 2: INTELLIGENT AUTOMATION SYSTEM
User Story 3: Zero-Decision Intelligent Creation
Goal: As a user, I want the system to automatically decide formatting, template, and organization so I never make manual formatting decisions.

Acceptance Criteria:

Automatic Template Selection:

System selects template with NO user input

Shows "Intelligent Format Selected: 'API Project Documentation' template"

Shows "(Matches 5 similar successful examples)"

Provides "Explain AI Choice" expandable section showing intelligence_reason

No template dropdown or selection UI

Automatic Title Generation:

System generates title from content analysis

Shows title as "Suggested Title: [API Service Setup & Configuration]"

Title field is editable ONLY via "Edit Title" button (not directly editable)

Title character counter and validation

Title shows "AI Suggested" badge

Automatic Structure Organization:

Multi-file content organized intelligently

Code before documentation, main files first

Related files grouped together

Shows "Intelligently combining 3 files as comprehensive documentation"

Confidence & Transparency:

Shows overall confidence score (94%)

Shows confidence breakdown: content_match, structure_match, context_match

"What made this intelligent:" section with detailed reasoning

Low confidence (<70%) shows "Intelligence Confidence Low" warning with fallback option

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/vscode-extension/src/confluence/intelligent-decisions.tsx

MODIFY:
- offline-folder-rag/edge_agent/app/agents/content_analysis_agent.py (add decision logic)
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py (add confidence scoring)
- offline-folder-rag/edge_agent/app/agents/formatting_agent.py (add template application)
- offline-folder-rag/edge_agent/app/agents/integration_agent.py (add title generation)
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceResults.tsx (add confidence display)
User Story 4: PRD-Compliant API Endpoints
Goal: As a system, I want to implement the exact API endpoints specified in the PRD for intelligent Confluence operations.

Acceptance Criteria:

Exact Endpoint Implementation:

POST /confluence/intelligent-analyze - Returns structured intelligence output

POST /confluence/intelligent-create - Creates page with AI intelligence

GET /confluence/intelligence-status - Check AI intelligence status

POST /confluence/intelligence-feedback - Provide feedback to improve AI intelligence

Request/response formats match PRD §9.0 EXACTLY

Intelligent-Analyze Endpoint:

Returns content analysis with detected patterns and confidence scores

Provides intelligent recommendations with template matching

Includes AI reasoning for all decisions

Returns confidence breakdown by category

Intelligent-Create Endpoint:

Creates Confluence page with full AI intelligence

Returns intelligence summary with AI decisions made

Provides confidence metrics for each intelligence operation

Returns created page metadata with intelligence tag

Error Responses:

Standardized error format with intelligence suggestions

Fallback options when intelligence fails

Clear guidance for error recovery

Files/Folders to Touch:

text
MODIFY:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (implement ALL 4 PRD endpoints)
- offline-folder-rag/edge_agent/app/api/schemas.py (add PRD schemas)
- offline-folder-rag/edge_agent/app/api/__init__.py (register routes)

NO CHANGES:
- offline-folder-rag/edge_agent/app/api/routes.py (Existing RAG endpoints)
GROUP 3: AGENT SYSTEM WITH LANGCHAIN INTEGRATION
User Story 5: 4-Agent Intelligent System
Goal: As a system, I want 4 specialized intelligent agents working together to automate Confluence page creation with zero user decisions.

Acceptance Criteria:

Content Analysis Agent:

Analyzes files in <3 seconds each

Detects: code language, structure, patterns, relationships

Uses AST parsing and NLP techniques

Outputs rich content profile with confidence scores

Integrates LangChain chains for enhanced analysis

Pattern Matching Agent (The AI Brain):

Uses vector similarity search across learned examples

Implements rule-based and statistical intelligence

Selects template in <2 seconds

Provides confidence scores with clear reasoning

Utilizes LangChain vector stores for template matching

Formatting Agent:

Template rendering with intelligent content placement

Automatic macro generation with context awareness

Accessibility compliance with intelligent alt text generation

Quality validation with auto-correction

Uses LangChain chains for structured formatting

Integration Agent:

Rate limiting with predictive intelligence

Error recovery with intelligent retry strategies

Progress tracking with ETA calculation

Result verification with validation

Handles Confluence API with LangChain tool integration

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/langchain/
  - chains/analysis_chain.py
  - chains/matching_chain.py
  - chains/formatting_chain.py
  - tools/confluence_tools.py

MODIFY:
- offline-folder-rag/edge_agent/app/agents/content_analysis_agent.py
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py
- offline-folder-rag/edge_agent/app/agents/formatting_agent.py
- offline-folder-rag/edge_agent/app/agents/integration_agent.py
- offline-folder-rag/edge_agent/app/agents/coordinator.py
User Story 6: Example-Based Intelligence with Export/Import
Goal: As a user, I want the system to learn from successful creations and allow export/import of learned examples for team sharing.

Acceptance Criteria:

Learning from Success:

Automatically stores successful creations as examples

Extracts patterns: content type, template used, success factors

Updates vector embeddings for similarity matching

Tracks improvement in matching accuracy

Shows "Learning Indicator" when system learns

Example Export:

Export learned examples as JSON file

Include: content profiles, templates, success metrics

Exclude sensitive data (file contents, user info)

Export by project, date range, or template type

Export format matches PRD specification

Example Import:

Import JSON files with learned examples

Validate import format and integrity

Merge with existing examples (avoid duplicates)

Update vector embeddings after import

Show "Intelligence Examples Imported: X new examples learned"

Team Intelligence Sharing:

Share examples across team members

Collective learning improves template matching

Maintain privacy: anonymize user data

Configurable: opt-in/out of sharing

Shows "Collective Intelligence: X examples from team"

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/example_manager.py
- offline-folder-rag/edge_agent/app/confluence/export_import.py
- confluence_data/examples/export_format.json

MODIFY:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (Add export/import endpoints)
- offline-folder-rag/edge_agent/app/agents/learning_agent.py
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFeedback.tsx
GROUP 4: MCP SERVER EXTENSION
User Story 7: MCP Server Task Extension
Goal: As a system, I want to extend the existing MCP Server to handle Confluence tasks alongside RAG tasks without duplication.

Acceptance Criteria:

Extend Existing MCP:

Add 4 new task types to existing MCP Server

Reuse existing task queue and orchestration

Same worker pool handles both RAG and Confluence tasks

Priority: RAG queries first, Confluence creation second

New Task Types:

confluence_intelligent_analyze - Analyze content with AI

confluence_intelligent_match - Find best template intelligently

confluence_intelligent_format - Apply formatting intelligently

confluence_intelligent_create - Create page with intelligence

Coexistence with RAG:

RAG tasks (rag_query, rag_search, rag_overview, rag_index) unchanged

Confluence tasks added to same queue

Resource sharing: CPU, memory, database connections

No performance impact on existing RAG tasks

Unified Progress Tracking:

Single progress system for all tasks

Status visible in chat interface

Task cancellation works for both types

Error handling consistent across task types

Files/Folders to Touch:

text
MODIFY:
- offline-folder-rag/edge_agent/app/mcp_server/task_queue.py (Add 4 new task types)
- offline-folder-rag/edge_agent/app/mcp_server/orchestrator.py
- offline-folder-rag/edge_agent/app/mcp_server/__init__.py
- offline-folder-rag/edge_agent/app/mcp_server/confluence_tasks.py

NO CHANGES:
- offline-folder-rag/edge_agent/app/mcp_server/ (Structure unchanged)
User Story 8: Performance-Compliant Implementation
Goal: As a user, I want Confluence operations to meet PRD performance targets without impacting existing RAG performance.

Acceptance Criteria:

PRD Performance Targets:

Content analysis: <3 seconds per file

Template selection: <2 seconds

Complete page creation: <15 seconds including API calls

Memory usage: ≤300MB during Confluence operations

UI responsiveness: No lag in chat interface

Optimization Strategies:

Caching: Analysis results cached by file hash

Parallel processing: Multiple files analyzed in parallel

Streaming: Large files processed in chunks

Background processing: Learning happens in background

Resource Management:

Reuse existing database connections

Share Ollama instances with RAG

Memory limits enforced per operation

CPU throttling during intensive operations

Monitoring & Alerts:

Performance metrics logged for every operation

Alerts if targets not met

Optimization suggestions based on metrics

Graceful degradation if resources limited

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/prd_monitor.py
- offline-folder-rag/edge_agent/app/confluence/optimizer.py

MODIFY:
- offline-folder-rag/edge_agent/app/agents/ (All agents optimized)
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
- offline-folder-rag/edge_agent/app/config/config.py
- offline-folder-rag/edge_agent/app/confluence/client.py
GROUP 5: DATABASE INTEGRATION
User Story 9: Database Extension
Goal: As a system, I want to add only the necessary tables to the existing PostgreSQL database without changing existing schemas.

Acceptance Criteria:

Minimal Schema Changes:

Add only 4 tables specified in PRD §8.1

Reuse existing database connection pool

No changes to existing RAG tables

No separate database instance

PRD Tables:

intelligent_templates - Stores templates with learning capabilities

intelligence_examples - Stores learning examples

intelligent_creations - Tracks all page creations

intelligence_learning - Tracks learning progress

Reuse Existing Infrastructure:

Use same PostgreSQL connection as RAG

Same connection pooling settings

Same backup/restore procedures

Same migration system

Performance:

Table queries optimized with indexes

Vector operations use pgvector extension

Connection overhead: <5% increase

No impact on existing RAG queries

Files/Folders to Touch:

text
CREATE:
- migrations/004_confluence_tables.sql

MODIFY:
- offline-folder-rag/edge_agent/app/config/config.py
- alembic/versions/ (Add migration)

NO CHANGES:
- Existing RAG database models/tables
User Story 10: Intelligent Configuration
Goal: As a user, I want to configure Confluence settings within the existing RAG settings interface without new panels.

Acceptance Criteria:

Existing Settings Integration:

Add Confluence section to existing RAG settings page

No new settings panel or tab

Settings appear under "Confluence" subsection

Uses existing VS Code settings UI components

Configuration Options:

Credentials: URL, email, API token (encrypted)

Default space per project type

Rate limiting settings (requests/minute)

Logging level for Confluence operations

Learning toggles (enable/disable)

Export/import location for examples

Intelligent Defaults:

Auto-detect Confluence Cloud vs Server from URL

Suggest spaces based on API response

Default rate limits based on Confluence edition

Learning enabled by default

"Intelligent Mode" enabled by default

Security:

Credentials encrypted at rest using existing RAG encryption

API tokens never appear in logs (masked)

HTTPS/TLS for all external API calls

Settings validated before saving

Test connection button available

Files/Folders to Touch:

text
MODIFY:
- offline-folder-rag/vscode-extension/package.json
- offline-folder-rag/vscode-extension/src/extension.ts
- offline-folder-rag/edge_agent/app/config/confluence_config.py
- offline-folder-rag/edge_agent/app/config/config.py

CREATE:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFeedback.tsx
GROUP 6: USER EXPERIENCE & ONBOARDING
User Story 11: 2-Minute Learning Curve
Goal: As a new user, I want to understand and use Confluence features within 2 minutes without training.

Acceptance Criteria:

Instant Understanding:

Button label: "💾 Save to Confluence" exactly as PRD

First click shows: "Select files for intelligent formatting"

Progress messages: "Creating Intelligent Documentation..."

Success message: "✅ Intelligent Documentation Created!"

Progressive Disclosure:

First use: Simple flow (file → create) with minimal options

Second use: Show confidence scores

Third use: Show "Explain AI Choice"

Advanced features hidden by default

Progressive intelligence introduction

Clear Guidance:

Error messages suggest specific actions

Success messages include next steps

Tooltips explain briefly

No technical jargon in UI

Onboarding:

First-time tooltip: "Click to save files with intelligent formatting"

Success encouragement: "Great! Intelligent formatting applied perfectly"

Learning indicator: "Intelligence learning from your successful creation"

Clear first-time explanations

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/vscode-extension/src/confluence/onboarding.tsx
- offline-folder-rag/vscode-extension/src/confluence/simple-language.json

MODIFY:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceResults.tsx
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
User Story 12: Right-Click & Command Palette Integration
Goal: As a power user, I want to access Confluence features via right-click and command palette while staying in chat interface.

Acceptance Criteria:

Right-Click Context Menu:

Option: "🤖 Save to Confluence" exactly as PRD

Subtext: "(AI will format perfectly)" exactly as PRD

Appears when text is selected in editor

Opens chat interface with selection pre-loaded

Shows: "Intelligent formatting selected code as Python function"

Command Palette Commands:

PRD: Save to Confluence (Intelligent)

PRD: Save Selection (AI Formatting)

PRD: Document Project Intelligently

PRD: View Intelligent Creations

PRD: Configure AI Settings

All commands open chat interface, not separate windows

Keyboard Shortcuts:

Configurable in VS Code keyboard shortcuts

Default: Ctrl+Shift+C for Confluence

Works with existing RAG shortcuts

Conflict detection with other extensions

Integration:

Commands use same chat interface as button

No duplication of functionality

Consistent user experience

All paths lead to chat interface

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/vscode-extension/src/confluence/commands.ts
- offline-folder-rag/vscode-extension/src/confluence/context-menu.ts

MODIFY:
- offline-folder-rag/vscode-extension/package.json
- offline-folder-rag/vscode-extension/src/extension.ts
GROUP 7: ERROR HANDLING & RELIABILITY
User Story 13: Intelligent Error Recovery
Goal: As a user, I want the system to handle errors intelligently with clear guidance and automatic recovery.

Acceptance Criteria:

Error Classification:

Network errors: "Can't reach Confluence, check connection"

Auth errors: "Invalid credentials, update in settings"

Rate limit: "Too many requests, retrying in 30 seconds"

Content errors: "AI could not determine optimal format"

Intelligent Recovery:

Network errors: Auto-retry 3 times with exponential backoff

Rate limits: Wait and retry automatically

Auth errors: Prompt to update credentials with "Update Settings" button

Content errors: Suggest alternative files

User Guidance:

Error messages in PRD format

Specific action buttons: "Update Settings", "Retry", "Cancel"

Help links to documentation

Fallback options when available

Reliability Metrics:

Success rate: >95%

Auto-recovery rate: >90% of errors

User intervention required: <10% of errors

Data integrity: No corruption on failure

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/error_handler.py
- offline-folder-rag/vscode-extension/src/confluence/error-messages.tsx

MODIFY:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
- offline-folder-rag/edge_agent/app/agents/integration_agent.py
- offline-folder-rag/edge_agent/app/confluence/client.py
User Story 14: Minimal Security Implementation
Goal: As a system, I want to implement only the security features specified in the PRD without scope inflation.

Acceptance Criteria:

PRD Security Requirements:

Credentials encrypted at rest (use existing RAG encryption)

API tokens never appear in logs (masked)

HTTPS/TLS for all external API calls

User data isolation between projects

No Additional Security:

No new authentication system (use existing)

No additional encryption layers

No separate audit logging (use existing)

No security scanning beyond PRD requirements

Implementation:

Reuse existing RAG credential store

Extend existing log masking for Confluence tokens

Use existing HTTP client with TLS

Project isolation via existing workspace mechanism

Verification:

Credentials encrypted in settings file

Token masking verified in log output

TLS verified for Confluence API calls

Workspace isolation tested

Files/Folders to Touch:

text
MODIFY:
- offline-folder-rag/edge_agent/app/config/config.py
- offline-folder-rag/edge_agent/app/logging/logger.py
- offline-folder-rag/edge_agent/app/confluence/client.py
GROUP 8: TESTING & VALIDATION
User Story 15: PRD Compliance Testing
Goal: As a QA engineer, I want comprehensive tests that verify all PRD requirements are met exactly.

Acceptance Criteria:

PRD Requirement Validation:

Test UR1: No new interfaces created

Test UR2: Zero manual decisions required

Test UR3: Maximum 3-click flow

Test UR4: Context-aware suggestions work

Test all FR1-FR6: Functional requirements met

Test all NFR1-NFR5: Non-functional requirements met

API Compliance Testing:

/confluence/intelligent-analyze returns exact PRD format

/confluence/intelligent-create returns exact PRD format

/confluence/intelligence-status returns exact PRD format

/confluence/intelligence-feedback returns exact PRD format

Error responses match PRD format

All fields present as specified

Performance Testing:

Content analysis: <3s/file (95th percentile)

Template selection: <2s (95th percentile)

Page creation: <15s (95th percentile)

Memory usage: ≤300MB peak

Learning curve: <2 minutes for new users

Integration Testing:

No impact on existing RAG functionality

MCP server extension works with existing tasks

Database extensions don't break existing queries

Settings integration doesn't break existing settings

RAG performance unchanged

Files/Folders to Touch:

text
CREATE:
- tests/confluence/test_prd_compliance.py
- tests/confluence/test_api_prd_format.py
- tests/confluence/test_performance_targets.py
- tests/confluence/test_intelligence_learning.py

MODIFY:
- pytest.ini
- .github/workflows/ci.yml
GROUP 9: ADVANCED FEATURES
User Story 16: Smart Project Documentation
Goal: As a user, I want to document entire projects with one command by typing /confluence document-project in chat.

Acceptance Criteria:

Command Trigger:

User types /confluence document-project in RAG chat

System responds: "Intelligently scanning project for documentation..."

Shows progress: "Analyzing project structure...", "Detecting key files..."

Intelligent Project Scan:

System scans project for key files intelligently

Determines project type (web app, API, library) automatically

Identifies: main source files, configuration, README, tests

Shows: "Detected: Python FastAPI project with 12 source files"

Project-Specific Intelligent Template:

Selects appropriate project template based on examples

Uses "Mixed Project Intelligence Template" for multi-file projects

Shows: "Selected 'API Project Intelligence Template' (Matches 8 examples)"

Comprehensive Documentation Creation:

Creates single, well-organized Confluence page

Includes: overview, architecture, setup, API endpoints, configuration

Returns link in chat with intelligent summary

Shows: "✅ Intelligent Project Documentation Created! [link]"

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/project_scanner.py
- offline-folder-rag/vscode-extension/src/confluence/project-documentation.tsx

MODIFY:
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py
- offline-folder-rag/vscode-extension/src/confluence/commands.ts
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
User Story 17: Intelligence Status & Feedback System
Goal: As a system, I want to implement the missing intelligence endpoints for status and feedback.

Acceptance Criteria:

Intelligence Status Endpoint:

GET /confluence/intelligence-status?detail_level=full

Returns: intelligence metrics, learning progress, improvement rates

Shows: "Intelligence Status: 94% accuracy, 247 examples learned"

Includes: template selection accuracy, user acceptance rate, learning rate

Intelligence Feedback Endpoint:

POST /confluence/intelligence-feedback

Request: {"creation_id": "uuid", "intelligence_score": 5, "feedback": "Perfect AI formatting!"}

Updates intelligence metrics and learning

Applies improvements to template matching

Returns: updated intelligence metrics

Intelligence Dashboard:

Command: PRD: View Intelligent Creations opens intelligence dashboard in chat

Shows: success rate, learning progress, template performance

Includes: "Intelligence Confidence: 94%", "Learning Rate: +15%"

Continuous Improvement:

Feedback improves future template matching

User ratings affect confidence scores

System learns from both success and feedback

Shows: "Intelligence Improved: Template matching accuracy increased to 96%"

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/edge_agent/app/confluence/status_manager.py
- offline-folder-rag/vscode-extension/src/confluence/intelligence-dashboard.tsx

MODIFY:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
- offline-folder-rag/edge_agent/app/agents/learning_agent.py
- offline-folder-rag/vscode-extension/src/confluence/commands.ts
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceAnalytics.tsx
User Story 18: Enhanced Intelligence Indicators
Goal: As a user, I want to see intelligence indicators for learning and template selection.

Acceptance Criteria:

Learning Indicator:

Shows when system learns from successful creation

Message: "🎓 Intelligence Learning: System learned from this successful creation"

Appears after successful page creation

Shows: "Added to 8 similar examples for future matching"

Intelligence Badge:

"AI-Formatted" badge appears on all successful creations

Badge appears in success message: "✅ Intelligent Documentation Created! [AI-Formatted]"

Badge appears in intelligence dashboard

Consistent branding across all interfaces

Template Intelligence Display:

Shows why specific template was selected

"Intelligent Format Selected: 'API Documentation' template"

Subtext: "(Detected FastAPI patterns, matches 5 examples with 97% success)"

Expandable "Explain AI Choice" section with detailed reasoning

Confidence Intelligence:

Confidence scores shown consistently (0-100%)

Color coding: Green (>90%), Yellow (70-90%), Red (<70%)

Tooltip: "Intelligence Confidence: How sure AI is about this decision"

Low confidence triggers "Intelligence Confidence Low" warning

Files/Folders to Touch:

text
CREATE:
- offline-folder-rag/vscode-extension/src/confluence/intelligence-indicators.tsx
- offline-folder-rag/vscode-extension/src/confluence/badges/

MODIFY:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceResults.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py
DIVISION OF USER STORIES AMONG 5 DEVELOPERS
ALEM (Frontend & UI/UX Specialist)
Focus: VS Code Extension UI, Chat Integration, User Experience

User Stories:

User Story 1: Chat-Only Confluence Integration - Primary UI integration

User Story 11: 2-Minute Learning Curve - Onboarding & progressive disclosure

User Story 12: Right-Click & Command Palette Integration - VS Code extension features

User Story 18: Enhanced Intelligence Indicators - UI badges, indicators, confidence display

Independent Testability:

Can test UI components locally in VS Code extension host

Can verify chat integration without backend by mocking responses

Can test right-click and command palette features independently

Can validate UI compliance with PRD visual designs

Files Alem Will Create/Modify:

text
FRONTEND COMPONENTS:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceButton.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceProgress.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceResults.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceAnalytics.tsx
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFeedback.tsx
- offline-folder-rag/vscode-extension/src/confluence/types.ts

UI/UX COMPONENTS:
- offline-folder-rag/vscode-extension/src/confluence/intelligence-indicators.tsx
- offline-folder-rag/vscode-extension/src/confluence/badges/
- offline-folder-rag/vscode-extension/src/confluence/onboarding.tsx
- offline-folder-rag/vscode-extension/src/confluence/simple-language.json
- offline-folder-rag/vscode-extension/src/confluence/error-messages.tsx

VS CODE INTEGRATION:
- offline-folder-rag/vscode-extension/src/confluence/commands.ts
- offline-folder-rag/vscode-extension/src/confluence/context-menu.ts
- offline-folder-rag/vscode-extension/src/extension.ts
- offline-folder-rag/vscode-extension/package.json
Alem's Deliverables:

Complete VS Code extension UI components

Chat interface integration with mock backend

Right-click context menu and command palette

Intelligence badges and visual indicators

Progressive onboarding experience

Error message display components

CHAITANYA (Frontend-Backend Integration Specialist)
Focus: Context-Aware Features, Configuration, Project Scanning

User Stories:

User Story 2: Context-Aware File Suggestions - Chat context integration

User Story 10: Intelligent Configuration - Settings integration

User Story 16: Smart Project Documentation - Project scanning feature

User Story 3: Zero-Decision Intelligent Creation - Integration with agents

Independent Testability:

Can test context analysis locally with sample chat histories

Can test settings integration without full backend

Can implement project scanner that works locally on file system

Can create mock intelligent decisions for frontend testing

Can validate configuration flow independently

Files Chaitanya Will Create/Modify:

text
CONTEXT & CONFIGURATION:
- offline-folder-rag/edge_agent/app/confluence/context_analyzer.py
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceContextMenu.tsx
- offline-folder-rag/edge_agent/app/config/confluence_config.py
- offline-folder-rag/edge_agent/app/config/config.py

PROJECT FEATURES:
- offline-folder-rag/edge_agent/app/confluence/project_scanner.py
- offline-folder-rag/vscode-extension/src/confluence/project-documentation.tsx

INTELLIGENT DECISIONS:
- offline-folder-rag/vscode-extension/src/confluence/intelligent-decisions.tsx
- offline-folder-rag/edge_agent/app/agents/integration_agent.py (title generation)

INTELLIGENCE DASHBOARD:
- offline-folder-rag/vscode-extension/src/confluence/intelligence-dashboard.tsx
- offline-folder-rag/edge_agent/app/confluence/status_manager.py

INTEGRATION:
- offline-folder-rag/vscode-extension/src/confluence/ConfluenceFileSelector.tsx
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (context endpoints)
Chaitanya's Deliverables:

Context-aware file suggestion system

Complete configuration management

Project scanning and documentation feature

Intelligent decision UI components

Integration between frontend context and backend analysis

Intelligence dashboard components

FAZLEEN (Backend & Agent System Specialist)
Focus: Core Agent System, API Endpoints, MCP Server, LangChain Integration

User Stories:

User Story 4: PRD-Compliant API Endpoints - Primary backend API

User Story 5: 4-Agent Intelligent System - Core agent logic with LangChain

User Story 7: MCP Server Task Extension - Task orchestration

User Story 17: Intelligence Status & Feedback - Monitoring endpoints

Independent Testability:

Can develop and test agents locally with mock data

Can implement and test API endpoints independently with Postman/curl

Can test MCP task queue with local workers

Can create standalone agent tests with sample files

Can validate API response formats against PRD exactly

Files Fazleen Will Create/Modify:

text
LANGCHAIN & AGENTS:
- offline-folder-rag/edge_agent/app/langchain/ (all LangChain setup)
- offline-folder-rag/edge_agent/app/agents/content_analysis_agent.py
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py
- offline-folder-rag/edge_agent/app/agents/formatting_agent.py
- offline-folder-rag/edge_agent/app/agents/coordinator.py

CORE API ENDPOINTS:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (ALL endpoints)
- offline-folder-rag/edge_agent/app/api/schemas.py
- offline-folder-rag/edge_agent/app/api/__init__.py

MCP SERVER EXTENSION:
- offline-folder-rag/edge_agent/app/mcp_server/task_queue.py
- offline-folder-rag/edge_agent/app/mcp_server/orchestrator.py
- offline-folder-rag/edge_agent/app/mcp_server/__init__.py
- offline-folder-rag/edge_agent/app/mcp_server/confluence_tasks.py

MONITORING & FEEDBACK:
- offline-folder-rag/edge_agent/app/api/confluence_routes.py (status/feedback)
- offline-folder-rag/edge_agent/app/agents/learning_agent.py
Fazleen's Deliverables:

Complete LangChain infrastructure setup

All 4 PRD API endpoints with exact response formats

Complete 4-agent intelligent system with coordination

MCP server extension with 4 new task types

Intelligence status and feedback API endpoints

Agent orchestration and task management

HEENA (Database & Learning System Specialist)
Focus: Database Schema, Learning System, Export/Import, Vector Stores

User Stories:

User Story 6: Example-Based Intelligence - Core learning system

User Story 9: Database Extension - Database schema implementation

User Story 17: Intelligence Status & Feedback - Data layer (shared)

Independent Testability:

Can create and test database migrations locally

Can implement learning system with local PostgreSQL instance

Can test export/import functionality with JSON files

Can validate database schemas against PRD exactly

Can test example management independently

Files Heena Will Create/Modify:

text
DATABASE SCHEMA:
- migrations/004_confluence_tables.sql
- alembic/versions/
- offline-folder-rag/edge_agent/app/config/config.py

LEARNING SYSTEM:
- offline-folder-rag/edge_agent/app/confluence/example_manager.py
- offline-folder-rag/edge_agent/app/confluence/export_import.py
- confluence_data/examples/export_format.json

INTELLIGENCE DATA LAYER:
- offline-folder-rag/edge_agent/app/agents/pattern_matching_agent.py (vector DB)
- offline-folder-rag/edge_agent/app/agents/learning_agent.py
- offline-folder-rag/edge_agent/app/langchain/vector_stores.py

DATA VALIDATION:
- Tests for database migrations
- Tests for export/import functionality
- Schema validation scripts

CONFIGURATION DATA:
- offline-folder-rag/edge_agent/app/config/confluence_config.py
Heena's Deliverables:

All 4 PRD database tables with exact schemas

Complete example-based learning system

Export/import functionality for team sharing

Vector embedding storage and retrieval

Database migrations and schema management

Learning data persistence layer

NAVEEN (Performance, Security & Testing Specialist)
Focus: Performance, Security, Error Handling, Testing Framework

User Stories:

User Story 8: Performance-Compliant Implementation - Performance optimization

User Story 13: Intelligent Error Recovery - Error handling system

User Story 14: Minimal Security Implementation - Security requirements

User Story 15: PRD Compliance Testing - Testing framework

User Story 3: Zero-Decision Intelligent Creation - Performance aspects (shared)

Independent Testability:

Can create performance tests that run locally

Can implement and test error handling independently

Can validate security features locally

Can develop comprehensive test suite

Can create mock scenarios for performance validation

Files Naveen Will Create/Modify:

text
PERFORMANCE OPTIMIZATION:
- offline-folder-rag/edge_agent/app/confluence/prd_monitor.py
- offline-folder-rag/edge_agent/app/confluence/optimizer.py
- offline-folder-rag/edge_agent/app/config/config.py
- offline-folder-rag/edge_agent/app/confluence/client.py

SECURITY IMPLEMENTATION:
- offline-folder-rag/edge_agent/app/logging/logger.py
- offline-folder-rag/edge_agent/app/confluence/client.py (HTTPS/TLS)
- offline-folder-rag/edge_agent/app/config/config.py

ERROR HANDLING:
- offline-folder-rag/edge_agent/app/confluence/error_handler.py
- offline-folder-rag/edge_agent/app/agents/integration_agent.py
- offline-folder-rag/edge_agent/app/api/confluence_routes.py

TESTING FRAMEWORK:
- tests/confluence/test_prd_compliance.py
- tests/confluence/test_api_prd_format.py
- tests/confluence/test_performance_targets.py
- tests/confluence/test_intelligence_learning.py
- tests/confluence/test_e2e_workflows.py
- tests/confluence/test_reliability.py
- tests/confluence/test_security_compliance.py
- pytest.ini
- .github/workflows/ci.yml

AGENT PERFORMANCE:
- offline-folder-rag/edge_agent/app/agents/ (optimization)
- offline-folder-rag/edge_agent/app/api/confluence_routes.py
Naveen's Deliverables:

Performance monitoring ensuring PRD targets

Complete security implementation per NFR3

Error handling and recovery system

Comprehensive PRD compliance test suite

CI/CD pipeline with automated testing

Performance optimization across all components

COLLABORATION POINTS & INTERDEPENDENCIES
Shared Components:
User Story 3: Zero-Decision Intelligent Creation

Chaitanya: UI components and frontend integration

Fazleen: Agent logic for intelligent decisions

Naveen: Performance optimization

User Story 17: Intelligence Status & Feedback

Fazleen: API endpoints for status/feedback

Heena: Data layer and storage

Chaitanya: Dashboard UI components

Key Dependencies:
Frontend-Backend Contracts:

Fazleen defines API schemas → Alem/Chaitanya implement frontend

Heena defines database schemas → Fazleen implements data access

LangChain Integration:

Fazleen sets up LangChain infrastructure → All agents use it

Heena sets up vector stores → Fazleen's agents use for matching

Configuration Flow:

Chaitanya implements settings UI → Naveen ensures security

Heena manages configuration persistence → Fazleen uses for runtime

Independent Testability Per Developer:
Alem: Test UI in VS Code extension host with mocked APIs

Chaitanya: Test context analyzer with local files and chat logs

Fazleen: Test agents with sample files and Postman API calls

Heena: Test database migrations and exports with local PostgreSQL

Naveen: Test performance and security with local test suites

Handoff Points:
Alem → Chaitanya: UI components ready for context integration

Chaitanya → Fazleen: Context data format for agent consumption

Fazleen → Heena: Agent outputs for learning system storage

Heena → Naveen: Database schemas for performance testing

Naveen → All: Test frameworks and performance benchmarks

This division ensures each developer has clear ownership, can work independently with local testability, and has minimal blocking dependencies. LangChain is integrated naturally where it provides value without being forced into every user story.



                                                                                    USER STORIES

Below is a **clean assignment of the 18 user stories** to your 5 developers (**Heena, Naveen, Aleem, Fazleen, Chaitaniya**) with **expected outcomes/outputs** that are **visible + testable** (manual + independent where possible).

---

# 1) Aleem — VS Code Chat UX Owner (UI-only)

## Assigned User Stories

* **US1** Chat-Only Confluence Integration
* **US11** 2-Minute Learning Curve
* **US12** Right-Click & Command Palette Integration *(UI wiring + chat-only constraint)*
* **US18** Enhanced Intelligence Indicators *(badges + confidence UI)*

## Expected outputs (what should exist after implementation)

### UI outputs (what user sees in chat)

* A **💾 Save to Confluence** button **adjacent to the Send button** in the existing chat input.
* Clicking it shows a **chat message** file selector (not a new panel/tab).
* After selection, chat shows:

  * **analysis card** (fields exactly as PRD)
  * **one updating progress message**
  * **success/failure card** in chat
* Visual indicators:

  * **AI-Formatted badge**
  * **confidence score + breakdown**
  * **learning indicator message**
  * **Explain AI Choice** expandable area (renders when present)

### Code outputs (deliverables)

* New/updated extension files under:

  * `offline-folder-rag/vscode-extension/src/confluence/`
  * `offline-folder-rag/vscode-extension/src/extension.ts`
  * `offline-folder-rag/vscode-extension/package.json`

### Independent manual test (Aleem can do alone)

* Run extension host → click button → see all chat-only UI flows using **mock responses** (no backend required yet).
* Confirm **no new panels/tabs/modals** are introduced.

---


# 2) Chaitaniya — Context + Config + Advanced Chat Commands

## Assigned User Stories

* **US2** Context-Aware File Suggestions
* **US10** Intelligent Configuration *(Confluence settings inside existing settings UI)*
* **US16** Smart Project Documentation *(chat command / slash command flow)*
* **US17** Intelligence Status & Feedback *(UI/dashboard side: “View Intelligent Creations” in chat)*

## Expected outputs

### User-visible outputs

* When user clicks **Save to Confluence**, file selector shows:

  * **“Based on your conversation”** pre-selected files (from last 5 messages)
  * **“Add related files”** option (imports/dependencies)
  * detected language badge like **“Detected: Python FastAPI”**
* Confluence preferences:

  * **space remembered per project folder**
  * shows **“Previously used: DEV”**
  * one-click space change dropdown
* Chat command:

  * `/confluence document-project` triggers:

    * “Scanning project…” progress messages
    * detected project type + key files summary
    * final success message with link (mockable)

### Code outputs

* Backend:

  * `offline-folder-rag/edge_agent/app/confluence/context_analyzer.py`
  * `offline-folder-rag/edge_agent/app/config/confluence_config.py`
* Extension:

  * `offline-folder-rag/vscode-extension/src/confluence/ConfluenceContextMenu.tsx`
  * updates inside `ConfluenceFileSelector.tsx`
  * chat commands UI pieces for project-doc + status dashboard

### Independent manual test

* Use a mock chat history + local repo:

  * Verify suggested files appear instantly
  * Verify space preference persists per folder
  * Verify slash command produces chat-only workflow

---

# 3) Fazleen — Core Backend Contracts + Agents + MCP (Engine Owner)

## Assigned User Stories

* **US4** PRD-Compliant API Endpoints *(ALL core endpoints)*
* **US5** 4-Agent Intelligent System *(LangChainintegration)*
* **US7** MCP Server Task Extension *(4 new task types + priority rules)*
* **US3** Zero-Decision Intelligent Creation *(backend decision outputs: title/template/structure/confidence)*

## Expected outputs

### API outputs (Postman/curl testable)

* Endpoints implemented and returning **exact PRD schema**:

  * `POST /confluence/intelligent-analyze`
  * `POST /confluence/intelligent-create`
  * `GET /confluence/intelligence-status`
  * `POST /confluence/intelligence-feedback`
* Error responses are standardized + include fallback guidance.

### Agent outputs (system outputs)

* Agent pipeline returns:

  * detected content profile
  * template decision + **reasoning**
  * title suggestion + edit constraints (UI enforces edit button)
  * structure grouping decisions
  * confidence score + breakdown

### MCP outputs

* Task queue supports Confluence tasks:

  * `confluence_intelligent_analyze`
  * `confluence_intelligent_match`
  * `confluence_intelligent_format`
  * `confluence_intelligent_create`
* Priority rule enforced: **RAG tasks first**, Confluence second.
* Unified progress + cancellation works.

### Code outputs

* `offline-folder-rag/edge_agent/app/api/confluence_routes.py`
* `offline-folder-rag/edge_agent/app/api/schemas.py`
* `offline-folder-rag/edge_agent/app/agents/*`
* `offline-folder-rag/edge_agent/app/mcp_server/*`
* `offline-folder-rag/edge_agent/app/langchain/*`

### Independent manual test

* Start edge agent → Postman verify responses.
* Run MCP locally → enqueue tasks → verify progress and cancellation.
* Run agent pipeline on fixtures without needing UI.

---

# 4) Heena — Database + Learning + Export/Import Owner

## Assigned User Stories

* **US9** Database Extension *(4 PRD tables only)*
* **US6** Example-Based Intelligence with Export/Import *(learned examples lifecycle)*
* **US17** Intelligence Status & Feedback *(data layer: store metrics, feedback, learning progress)*

## Expected outputs

### Database outputs

* Migration(s) created and verified:

  * 4 tables exactly:

    * `intelligent_templates`
    * `intelligence_examples`
    * `intelligent_creations`
    * `intelligence_learning`
* Proper indexes (including vector index if used).
* No changes to existing RAG tables.

### Learning outputs

* On successful creation:

  * system stores an example profile (no raw file contents)
  * embeddings updated/refreshed (per chosen store)
  * learning progress updated

### Export/Import outputs

* Export examples to JSON:

  * includes metadata, profiles, metrics
  * excludes sensitive contents
* Import validates and merges:

  * dedupe logic
  * integrity checks
  * post-import embedding refresh

### Code outputs

* `migrations/004_confluence_tables.sql` (or aligned numbering)
* `offline-folder-rag/edge_agent/app/confluence/example_manager.py`
* `offline-folder-rag/edge_agent/app/confluence/export_import.py`
* `confluence_data/examples/export_format.json`

### Independent manual test

* Run migration locally.
* Insert examples → export → delete local copy → import → verify counts + dedupe.

---

# 5) Naveen — Performance + Security + Error Recovery + PRD Compliance Tests

## Assigned User Stories

* **US8** Performance-Compliant Implementation
* **US13** Intelligent Error Recovery
* **US14** Minimal Security Implementation
* **US15** PRD Compliance Testing *(the enforcement net for all stories)*

## Expected outputs

### Performance outputs (measured)

* Meets PRD targets:

  * analysis **<3s/file (p95)**
  * template select **<2s (p95)**
  * create **<15s (p95)**
  * memory **≤300MB peak**
* Caching by file hash + parallel analysis logic (as per story).
* Monitoring logs/metrics emitted per operation.

### Reliability outputs

* Error classification messages (chat-friendly):

  * network/auth/rate-limit/content errors
* Auto-retry behaviors:

  * network retry 3 times with backoff
  * rate-limit wait and retry automatically
* “Update Settings / Retry / Cancel” action options in responses.

### Security outputs

* Credentials encrypted at rest (reuse existing mechanism)
* Token masking in logs verified
* HTTPS/TLS enforced for Confluence calls
* project isolation enforced

### Test outputs

* Test suites created and runnable:

  * `tests/confluence/test_prd_compliance.py`
  * `tests/confluence/test_api_prd_format.py`
  * `tests/confluence/test_performance_targets.py`
  * `tests/confluence/test_intelligence_learning.py`
  * plus E2E/reliability/security tests if you included them
* CI updated to run these without breaking RAG CI.

### Independent manual test

* Force failures (bad token / offline / 429) and verify recovery.
* Run pytest locally; confirm PRD compliance tests catch UI/contract drift.

---

# Cross-team “handoff outputs” (so everyone stays unblocked)

## Fazleen → Aleem/Chaitaniya/Naveen

* **Sample JSON fixtures** for all 4 endpoints (success + errors) so UI and tests can proceed without waiting.

## Heena → Fazleen/Naveen

* DB migration + schema notes + seed data + example export format.

## Chaitaniya → Aleem/Naveen

* Mock chat-history fixtures and context analyzer output shape.

## Naveen → Everyone

* PRD compliance test checklist + “definition of done” gates.

---

## Final expected product outcome (what you, as founder, will see end-to-end)

1. In the existing RAG chat input, you see **💾 Save to Confluence**.
2. You click it → chat shows file selector → you choose files.
3. System shows analysis + template choice + confidence (no manual template selection).
4. You click **Create Perfect Page** → progress updates in chat → success message with Confluence page link.
5. System stores an example (optional) and status/feedback endpoints show learning progress.
6. Performance + security rules are enforced; PRD compliance tests prevent drift.

If you want, I can convert the above into a **one-page team execution board**:
**Developer → Stories → Deliverables → Manual Test Steps → “Done” criteria** (so interns can execute with zero confusion).
