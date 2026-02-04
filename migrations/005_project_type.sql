-- US-16: Add project_type to intelligent_creations for project documentation tracking
-- Idempotent: safe to run multiple times

ALTER TABLE intelligent_creations ADD COLUMN IF NOT EXISTS project_type VARCHAR(50);
