-- Confluence config: user/project settings and config history (PRD §5.2, Stories)
-- Idempotent: CREATE TABLE IF NOT EXISTS

-- User settings (encrypted at rest; sensitive values in setting_value_encrypted)
CREATE TABLE IF NOT EXISTS confluence_user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    setting_key VARCHAR(255) NOT NULL,
    setting_value_encrypted BYTEA NOT NULL,
    setting_type VARCHAR(50) NOT NULL,
    is_sensitive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, setting_key)
);

-- Project-specific settings (non-sensitive; JSONB)
CREATE TABLE IF NOT EXISTS confluence_project_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_path_hash VARCHAR(64) NOT NULL,
    setting_key VARCHAR(255) NOT NULL,
    setting_value JSONB NOT NULL,
    inherits_from_user BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_path_hash, setting_key)
);

-- Configuration change history (audit; hashes only, no plaintext values)
CREATE TABLE IF NOT EXISTS confluence_config_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    setting_key VARCHAR(255) NOT NULL,
    old_value_hash VARCHAR(64),
    new_value_hash VARCHAR(64),
    changed_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_confluence_user_settings_user_id ON confluence_user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_confluence_project_settings_project_hash ON confluence_project_settings(project_path_hash);
CREATE INDEX IF NOT EXISTS idx_confluence_config_history_user_changed ON confluence_config_history(user_id, changed_at);
