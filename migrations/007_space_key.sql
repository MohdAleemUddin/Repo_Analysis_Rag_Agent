-- US-2: Add space_key to intelligent_creations for per-project space preference (PRD §8.1)
-- Idempotent: safe to run multiple times

ALTER TABLE intelligent_creations ADD COLUMN IF NOT EXISTS space_key VARCHAR(50);
CREATE INDEX IF NOT EXISTS idx_intelligent_creations_space_key ON intelligent_creations(space_key);
