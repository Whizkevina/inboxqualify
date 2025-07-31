-- InboxQualify Supabase PostgreSQL Migration Script
-- Run this SQL in your Supabase SQL Editor to create all required tables

-- Enable Row Level Security (RLS) for security
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- Create tables
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address TEXT,
    email_content TEXT,
    sender_name TEXT,
    sender_email TEXT,
    score INTEGER,
    response_time REAL,
    ai_model TEXT DEFAULT 'gemini',
    error_message TEXT,
    classification JSONB
);

CREATE TABLE IF NOT EXISTS public.admin_users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS public.admin_audit_log (
    id BIGSERIAL PRIMARY KEY,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.alert_settings (
    id BIGSERIAL PRIMARY KEY,
    alert_type TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    threshold_value REAL,
    email_recipients TEXT[],
    last_triggered TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON public.usage_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_logs_ip ON public.usage_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_usage_logs_score ON public.usage_logs(score);
CREATE INDEX IF NOT EXISTS idx_admin_audit_timestamp ON public.admin_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON public.admin_users(username);

-- Create helpful database functions
CREATE OR REPLACE FUNCTION get_average_score()
RETURNS REAL AS $$
BEGIN
    RETURN (SELECT COALESCE(AVG(score), 0) FROM public.usage_logs WHERE score IS NOT NULL);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_unique_ip_count()
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(DISTINCT ip_address) FROM public.usage_logs WHERE ip_address IS NOT NULL);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_error_rate()
RETURNS REAL AS $$
DECLARE
    total_count INTEGER;
    error_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM public.usage_logs;
    SELECT COUNT(*) INTO error_count FROM public.usage_logs WHERE error_message IS NOT NULL;
    
    IF total_count = 0 THEN
        RETURN 0;
    ELSE
        RETURN (error_count::REAL / total_count::REAL) * 100;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create RLS policies (optional, for additional security)
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_settings ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role full access
CREATE POLICY "Service role can manage usage_logs" ON public.usage_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage admin_users" ON public.admin_users
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage admin_audit_log" ON public.admin_audit_log
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage alert_settings" ON public.alert_settings
    FOR ALL USING (auth.role() = 'service_role');

-- Insert default alert settings
INSERT INTO public.alert_settings (alert_type, is_enabled, threshold_value, email_recipients)
VALUES 
    ('error_rate', true, 10.0, ARRAY['admin@yourcompany.com']),
    ('usage_spike', true, 3.0, ARRAY['admin@yourcompany.com']),
    ('api_failure', true, 5.0, ARRAY['admin@yourcompany.com'])
ON CONFLICT DO NOTHING;

-- Create a view for analytics dashboard
CREATE OR REPLACE VIEW public.analytics_summary AS
SELECT 
    COUNT(*) as total_requests,
    COUNT(DISTINCT ip_address) as unique_ips,
    AVG(score) as average_score,
    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count,
    (COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END)::REAL / COUNT(*)::REAL * 100) as error_rate,
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as hourly_requests
FROM public.usage_logs
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

COMMENT ON TABLE public.usage_logs IS 'Stores all email analysis requests and results';
COMMENT ON TABLE public.admin_users IS 'Admin user accounts for dashboard access';
COMMENT ON TABLE public.admin_audit_log IS 'Audit trail for all admin actions';
COMMENT ON TABLE public.alert_settings IS 'Configuration for email alert system';
