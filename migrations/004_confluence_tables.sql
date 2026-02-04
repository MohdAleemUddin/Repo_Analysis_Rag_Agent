-- PRD §8.1: Confluence intelligence tables (PostgreSQL + pgvector)
-- Same PostgreSQL instance as RAG; no changes to existing RAG tables.
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: intelligent_templates - Stores templates with learning capabilities
CREATE TABLE IF NOT EXISTS intelligent_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL,
    language VARCHAR(50),
    template_content TEXT NOT NULL,
    is_intelligent BOOLEAN DEFAULT true,
    source_examples JSONB,
    intelligence_score DECIMAL(3,2),
    success_rate DECIMAL(5,4) DEFAULT 1.0,
    confidence_avg DECIMAL(3,2),
    intelligence_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    intelligence_updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intelligence_embedding ON intelligent_templates
USING ivfflat (intelligence_embedding vector_cosine_ops) WITH (lists = 100);

-- Table: intelligence_examples - Stores learning examples
CREATE TABLE IF NOT EXISTS intelligence_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_profile JSONB NOT NULL,
    template_used UUID REFERENCES intelligent_templates(id),
    created_page_url TEXT,
    intelligence_metrics JSONB,
    learned_at TIMESTAMP DEFAULT NOW(),
    intelligence_embedding VECTOR(1536),
    confidence_score DECIMAL(3,2),
    user_feedback INTEGER,
    improvement_suggestions TEXT[]
);

CREATE INDEX IF NOT EXISTS idx_intelligence_embedding_examples ON intelligence_examples
USING ivfflat (intelligence_embedding vector_cosine_ops) WITH (lists = 100);

-- Table: intelligent_creations - Tracks all page creations (PRD typo "PRIMARY DEFAULT" fixed to PRIMARY KEY)
CREATE TABLE IF NOT EXISTS intelligent_creations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    project_path VARCHAR(1000),
    files_included TEXT[],
    content_intelligence JSONB,
    selected_template UUID REFERENCES intelligent_templates(id),
    intelligence_confidence DECIMAL(3,2),
    intelligence_reasoning TEXT,
    confluence_page_id VARCHAR(255),
    confluence_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    intelligence_score DECIMAL(3,2),
    user_satisfaction INTEGER,
    auto_improvement_applied BOOLEAN DEFAULT false
);

-- Table: intelligence_learning - Tracks learning progress
CREATE TABLE IF NOT EXISTS intelligence_learning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_type VARCHAR(50),
    before_score DECIMAL(3,2),
    after_score DECIMAL(3,2),
    improvement DECIMAL(3,2),
    learned_from UUID REFERENCES intelligent_creations(id),
    learned_at TIMESTAMP DEFAULT NOW(),
    learning_confidence DECIMAL(3,2),
    application_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4)
);

-- PRD §8.2: Initial intelligent data (pre-loaded templates and seed examples)
-- Idempotent: use fixed UUIDs and ON CONFLICT DO NOTHING where applicable.

-- 7 pre-loaded intelligent templates (PRD §8.2)
INSERT INTO intelligent_templates (id, name, description, content_type, language, template_content, is_intelligent, intelligence_score, confidence_avg)
VALUES
    ('a0000001-0001-4000-8000-000000000001'::uuid, 'Python API Intelligence Template', 'Learned from successful API documentation', 'python_api', 'python', '<p>API documentation template</p>', true, 0.92, 0.90),
    ('a0000001-0001-4000-8000-000000000002'::uuid, 'Web Application Intelligence Template', 'Learned from frontend projects', 'web_app', 'javascript', '<p>Web application documentation template</p>', true, 0.90, 0.88),
    ('a0000001-0001-4000-8000-000000000003'::uuid, 'Configuration Intelligence Template', 'Learned from infrastructure code', 'configuration', NULL, '<p>Configuration documentation template</p>', true, 0.88, 0.85),
    ('a0000001-0001-4000-8000-000000000004'::uuid, 'Database Intelligence Template', 'Learned from schema documentation', 'database', NULL, '<p>Database schema documentation template</p>', true, 0.89, 0.86),
    ('a0000001-0001-4000-8000-000000000005'::uuid, 'Mixed Project Intelligence Template', 'Learned from complete projects', 'mixed', NULL, '<p>Mixed project documentation template</p>', true, 0.91, 0.89),
    ('a0000001-0001-4000-8000-000000000006'::uuid, 'Library Intelligence Template', 'Learned from package documentation', 'library', NULL, '<p>Library documentation template</p>', true, 0.87, 0.84),
    ('a0000001-0001-4000-8000-000000000007'::uuid, 'Testing Intelligence Template', 'Learned from test documentation', 'testing', NULL, '<p>Testing documentation template</p>', true, 0.86, 0.83)
ON CONFLICT (id) DO NOTHING;

-- Seed intelligence_examples (minimal set; 50+ can be expanded by script or future seed)
INSERT INTO intelligence_examples (id, content_profile, template_used, intelligence_metrics, confidence_score)
SELECT
    'b0000001-0001-4000-8000-000000000001'::uuid,
    '{"content_types": ["python_api"], "detected_patterns": ["fastapi", "rest"]}'::jsonb,
    'a0000001-0001-4000-8000-000000000001'::uuid,
    '{"success": true}'::jsonb,
    0.94
WHERE NOT EXISTS (SELECT 1 FROM intelligence_examples WHERE id = 'b0000001-0001-4000-8000-000000000001'::uuid);

INSERT INTO intelligence_examples (id, content_profile, template_used, intelligence_metrics, confidence_score)
SELECT
    'b0000001-0001-4000-8000-000000000002'::uuid,
    '{"content_types": ["web_app"], "detected_patterns": ["react", "frontend"]}'::jsonb,
    'a0000001-0001-4000-8000-000000000002'::uuid,
    '{"success": true}'::jsonb,
    0.91
WHERE NOT EXISTS (SELECT 1 FROM intelligence_examples WHERE id = 'b0000001-0001-4000-8000-000000000002'::uuid);

INSERT INTO intelligence_examples (id, content_profile, template_used, intelligence_metrics, confidence_score)
SELECT
    'b0000001-0001-4000-8000-000000000003'::uuid,
    '{"content_types": ["configuration"], "detected_patterns": ["yaml", "docker"]}'::jsonb,
    'a0000001-0001-4000-8000-000000000003'::uuid,
    '{"success": true}'::jsonb,
    0.88
WHERE NOT EXISTS (SELECT 1 FROM intelligence_examples WHERE id = 'b0000001-0001-4000-8000-000000000003'::uuid);

INSERT INTO intelligence_examples (id, content_profile, template_used, intelligence_metrics, confidence_score)
SELECT
    'b0000001-0001-4000-8000-000000000004'::uuid,
    '{"content_types": ["mixed"], "detected_patterns": ["readme", "api", "config"]}'::jsonb,
    'a0000001-0001-4000-8000-000000000005'::uuid,
    '{"success": true}'::jsonb,
    0.90
WHERE NOT EXISTS (SELECT 1 FROM intelligence_examples WHERE id = 'b0000001-0001-4000-8000-000000000004'::uuid);

-- PRD §8.2: 50+ pre-analyzed successful documentation examples (rows 5-50)
INSERT INTO intelligence_examples (id, content_profile, template_used, intelligence_metrics, confidence_score)
SELECT * FROM (VALUES
    ('b0000001-0001-4000-8000-000000000005'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["flask", "endpoints"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.93),
    ('b0000001-0001-4000-8000-000000000006'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["django", "views"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000007'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["vue", "components"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000008'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["angular", "modules"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000009'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["env", "settings"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000010'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["kubernetes", "deploy"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.90),
    ('b0000001-0001-4000-8000-000000000011'::uuid, '{"content_types": ["database"], "detected_patterns": ["postgres", "migrations"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.92),
    ('b0000001-0001-4000-8000-000000000012'::uuid, '{"content_types": ["database"], "detected_patterns": ["sqlalchemy", "models"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000013'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["api", "readme", "config"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000014'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["service", "docs"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000015'::uuid, '{"content_types": ["library"], "detected_patterns": ["package", "exports"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.86),
    ('b0000001-0001-4000-8000-000000000016'::uuid, '{"content_types": ["library"], "detected_patterns": ["sdk", "client"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000017'::uuid, '{"content_types": ["testing"], "detected_patterns": ["pytest", "fixtures"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.90),
    ('b0000001-0001-4000-8000-000000000018'::uuid, '{"content_types": ["testing"], "detected_patterns": ["unittest", "mocks"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.85),
    ('b0000001-0001-4000-8000-000000000019'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["grpc", "proto"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.92),
    ('b0000001-0001-4000-8000-000000000020'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["async", "aiohttp"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000021'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["svelte", "stores"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000022'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["next", "pages"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000023'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["terraform", "infra"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000024'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["ansible", "playbooks"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.86),
    ('b0000001-0001-4000-8000-000000000025'::uuid, '{"content_types": ["database"], "detected_patterns": ["redis", "cache"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000026'::uuid, '{"content_types": ["database"], "detected_patterns": ["mongodb", "collections"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.90),
    ('b0000001-0001-4000-8000-000000000027'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["microservice", "api", "config"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.93),
    ('b0000001-0001-4000-8000-000000000028'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["monorepo", "packages"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000029'::uuid, '{"content_types": ["library"], "detected_patterns": ["utils", "helpers"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.85),
    ('b0000001-0001-4000-8000-000000000030'::uuid, '{"content_types": ["library"], "detected_patterns": ["plugin", "hooks"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000031'::uuid, '{"content_types": ["testing"], "detected_patterns": ["jest", "snapshots"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000032'::uuid, '{"content_types": ["testing"], "detected_patterns": ["coverage", "integration"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.90),
    ('b0000001-0001-4000-8000-000000000033'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["celery", "tasks"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.86),
    ('b0000001-0001-4000-8000-000000000034'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["websocket", "realtime"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000035'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["tailwind", "components"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000036'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["storybook", "design"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000037'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["nginx", "proxy"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000038'::uuid, '{"content_types": ["configuration"], "detected_patterns": ["ci", "github-actions"]}'::jsonb, 'a0000001-0001-4000-8000-000000000003'::uuid, '{"success": true}'::jsonb, 0.92),
    ('b0000001-0001-4000-8000-000000000039'::uuid, '{"content_types": ["database"], "detected_patterns": ["elasticsearch", "index"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000040'::uuid, '{"content_types": ["database"], "detected_patterns": ["graphql", "schema"]}'::jsonb, 'a0000001-0001-4000-8000-000000000004'::uuid, '{"success": true}'::jsonb, 0.90),
    ('b0000001-0001-4000-8000-000000000041'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["fullstack", "api", "ui"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000042'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["docs", "examples", "tests"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000043'::uuid, '{"content_types": ["library"], "detected_patterns": ["middleware", "auth"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000044'::uuid, '{"content_types": ["library"], "detected_patterns": ["logging", "metrics"]}'::jsonb, 'a0000001-0001-4000-8000-000000000006'::uuid, '{"success": true}'::jsonb, 0.86),
    ('b0000001-0001-4000-8000-000000000045'::uuid, '{"content_types": ["testing"], "detected_patterns": ["e2e", "playwright"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.91),
    ('b0000001-0001-4000-8000-000000000046'::uuid, '{"content_types": ["testing"], "detected_patterns": ["load", "locust"]}'::jsonb, 'a0000001-0001-4000-8000-000000000007'::uuid, '{"success": true}'::jsonb, 0.87),
    ('b0000001-0001-4000-8000-000000000047'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["openapi", "swagger"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.94),
    ('b0000001-0001-4000-8000-000000000048'::uuid, '{"content_types": ["python_api"], "detected_patterns": ["graphql", "resolvers"]}'::jsonb, 'a0000001-0001-4000-8000-000000000001'::uuid, '{"success": true}'::jsonb, 0.89),
    ('b0000001-0001-4000-8000-000000000049'::uuid, '{"content_types": ["web_app"], "detected_patterns": ["ssr", "hydration"]}'::jsonb, 'a0000001-0001-4000-8000-000000000002'::uuid, '{"success": true}'::jsonb, 0.88),
    ('b0000001-0001-4000-8000-000000000050'::uuid, '{"content_types": ["mixed"], "detected_patterns": ["devops", "docs", "api"]}'::jsonb, 'a0000001-0001-4000-8000-000000000005'::uuid, '{"success": true}'::jsonb, 0.92)
) AS v(id, content_profile, template_used, intelligence_metrics, confidence_score)
ON CONFLICT (id) DO NOTHING;
