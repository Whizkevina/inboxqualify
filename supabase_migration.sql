
        -- Create usage_logs table
        CREATE TABLE IF NOT EXISTS usage_logs (
            id SERIAL PRIMARY KEY,
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

        -- Create admin_users table
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE
        );

        -- Create admin_audit_log table
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id SERIAL PRIMARY KEY,
            admin_username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create alert_settings table
        CREATE TABLE IF NOT EXISTS alert_settings (
            id SERIAL PRIMARY KEY,
            alert_type TEXT NOT NULL,
            is_enabled BOOLEAN DEFAULT true,
            threshold_value REAL,
            email_recipients TEXT[],
            last_triggered TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON usage_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_usage_logs_ip ON usage_logs(ip_address);
        CREATE INDEX IF NOT EXISTS idx_usage_logs_score ON usage_logs(score);
        CREATE INDEX IF NOT EXISTS idx_admin_audit_timestamp ON admin_audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
        