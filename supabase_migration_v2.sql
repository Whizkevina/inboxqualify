-- Migration V2: Add support for Campaigns, Batches, and System Settings

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

-- 2. Batches Table
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    summary JSONB, -- Stores summary stats like average_score, total_emails, etc.
    original_filename TEXT,
    status TEXT DEFAULT 'completed'
);

-- 3. Batch Items Table (Individual Email Results)
CREATE TABLE IF NOT EXISTS batch_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    email_data JSONB, -- Stores subject, body, sender info
    analysis_result JSONB, -- Stores score, breakdown, suggestions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. System Settings Table (for Alert Configuration)
-- We use a single row with a specific key to store the global config
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_batches_campaign_id ON batches(campaign_id);
CREATE INDEX IF NOT EXISTS idx_batch_items_batch_id ON batch_items(batch_id);
