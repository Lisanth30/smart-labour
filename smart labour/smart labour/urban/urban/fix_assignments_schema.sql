-- Add missing columns to Assignments table (MySQL)
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS eta TIMESTAMP NULL;
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS started_at TIMESTAMP NULL;
