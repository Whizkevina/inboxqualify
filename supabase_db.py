"""
Supabase PostgreSQL Database Configuration for InboxQualify
Enhanced database management with cloud PostgreSQL for seamless deployment
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class SupabaseDB:
    def __init__(self):
        """Initialize Supabase client with configuration from environment variables"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for admin operations
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize database schema on first connection
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize all required tables in Supabase PostgreSQL"""
        try:
            # Create usage_logs table
            self.supabase.table('usage_logs').select('id').limit(1).execute()
        except Exception:
            # Tables don't exist, create them
            self.create_tables()
    
    def create_tables(self):
        """Create all required tables using Supabase SQL functions"""
        print("🔧 Creating Supabase database tables...")
        
        # Note: In production, you would run these SQL commands in Supabase SQL Editor
        # For now, we'll create a migration script
        migration_sql = """
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
        """
        
        # Save migration script for manual execution
        with open('supabase_migration.sql', 'w') as f:
            f.write(migration_sql)
        
        print("📝 Migration SQL created in 'supabase_migration.sql'")
        print("📋 Please run this SQL in your Supabase SQL Editor to create the tables")
    
    def log_email_analysis(self, ip_address: str, email_content: str, sender_name: str, 
                          sender_email: str, score: int, response_time: float, 
                          ai_model: str = "gemini", error_message: str = None, 
                          classification: dict = None):
        """Log email analysis to Supabase PostgreSQL"""
        try:
            data = {
                "ip_address": ip_address,
                "email_content": email_content,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "score": score,
                "response_time": response_time,
                "ai_model": ai_model,
                "error_message": error_message,
                "classification": json.dumps(classification) if classification else None
            }
            
            result = self.supabase.table('usage_logs').insert(data).execute()
            return result.data[0]['id'] if result.data else None
            
        except Exception as e:
            print(f"❌ Error logging to Supabase: {str(e)}")
            return None
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics from Supabase"""
        try:
            # Total requests
            total_result = self.supabase.table('usage_logs').select('id', count='exact').execute()
            total_requests = total_result.count
            
            # Today's requests
            today = datetime.now().date()
            today_result = self.supabase.table('usage_logs')\
                .select('id', count='exact')\
                .gte('timestamp', today.isoformat())\
                .execute()
            today_requests = today_result.count
            
            # Average score
            avg_result = self.supabase.rpc('get_average_score').execute()
            avg_score = avg_result.data if avg_result.data else 0
            
            # Error rate
            error_result = self.supabase.table('usage_logs')\
                .select('id', count='exact')\
                .not_.is_('error_message', 'null')\
                .execute()
            error_count = error_result.count
            
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "total_requests": total_requests,
                "today_requests": today_requests,
                "average_score": round(avg_score, 2),
                "error_rate": round(error_rate, 2),
                "unique_ips": self.get_unique_ip_count(),
                "last_24h_requests": self.get_recent_requests_count(24)
            }
            
        except Exception as e:
            print(f"❌ Error getting usage stats: {str(e)}")
            return {
                "total_requests": 0,
                "today_requests": 0,
                "average_score": 0,
                "error_rate": 0,
                "unique_ips": 0,
                "last_24h_requests": 0
            }
    
    def get_usage_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent usage logs from Supabase"""
        try:
            result = self.supabase.table('usage_logs')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"❌ Error getting usage logs: {str(e)}")
            return []
    
    def get_advanced_analytics(self, start_date: str = None, end_date: str = None,
                             ip_filter: str = None, min_score: int = None, 
                             max_score: int = None) -> Dict[str, Any]:
        """Get advanced analytics with filtering from Supabase"""
        try:
            query = self.supabase.table('usage_logs').select('*')
            
            # Apply filters
            if start_date:
                query = query.gte('timestamp', start_date)
            if end_date:
                query = query.lte('timestamp', end_date)
            if ip_filter:
                query = query.eq('ip_address', ip_filter)
            if min_score is not None:
                query = query.gte('score', min_score)
            if max_score is not None:
                query = query.lte('score', max_score)
            
            result = query.execute()
            logs = result.data
            
            if not logs:
                return {"filtered_requests": 0, "score_stats": {}, "hourly_data": []}
            
            # Calculate statistics
            scores = [log['score'] for log in logs if log['score'] is not None]
            
            score_stats = {
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "avg_score": sum(scores) / len(scores) if scores else 0,
                "total_requests": len(logs)
            }
            
            # Hourly distribution
            hourly_data = {}
            for log in logs:
                if log['timestamp']:
                    hour = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).hour
                    hourly_data[hour] = hourly_data.get(hour, 0) + 1
            
            hourly_list = [{"hour": h, "requests": hourly_data.get(h, 0)} for h in range(24)]
            
            return {
                "filtered_requests": len(logs),
                "score_stats": score_stats,
                "hourly_data": hourly_list,
                "unique_ips": len(set(log['ip_address'] for log in logs if log['ip_address'])),
                "error_count": len([log for log in logs if log['error_message']])
            }
            
        except Exception as e:
            print(f"❌ Error getting advanced analytics: {str(e)}")
            return {"filtered_requests": 0, "score_stats": {}, "hourly_data": []}
    
    def clear_old_data(self, days_old: int = 30) -> int:
        """Clear data older than specified days from Supabase"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            result = self.supabase.table('usage_logs')\
                .delete()\
                .lt('timestamp', cutoff_date.isoformat())\
                .execute()
            
            return len(result.data) if result.data else 0
            
        except Exception as e:
            print(f"❌ Error clearing old data: {str(e)}")
            return 0
    
    # Admin User Management Methods
    def create_admin_user(self, username: str, password: str, email: str, role: str = "admin") -> bool:
        """Create new admin user in Supabase"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            data = {
                "username": username,
                "password_hash": password_hash,
                "email": email,
                "role": role
            }
            
            result = self.supabase.table('admin_users').insert(data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error creating admin user: {str(e)}")
            return False
    
    def verify_admin_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify admin user credentials against Supabase"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            result = self.supabase.table('admin_users')\
                .select('*')\
                .eq('username', username)\
                .eq('password_hash', password_hash)\
                .eq('is_active', True)\
                .execute()
            
            if result.data:
                user = result.data[0]
                # Update last login
                self.supabase.table('admin_users')\
                    .update({"last_login": datetime.now().isoformat()})\
                    .eq('id', user['id'])\
                    .execute()
                return user
            
            return None
            
        except Exception as e:
            print(f"❌ Error verifying admin user: {str(e)}")
            return None
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        """Get all admin users from Supabase"""
        try:
            result = self.supabase.table('admin_users')\
                .select('id', 'username', 'email', 'role', 'is_active', 'created_at', 'last_login')\
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"❌ Error getting admin users: {str(e)}")
            return []
    
    def log_admin_action(self, admin_username: str, action: str, details: str = None, ip_address: str = None):
        """Log admin action to audit trail in Supabase"""
        try:
            data = {
                "admin_username": admin_username,
                "action": action,
                "details": details,
                "ip_address": ip_address
            }
            
            self.supabase.table('admin_audit_log').insert(data).execute()
            
        except Exception as e:
            print(f"❌ Error logging admin action: {str(e)}")
    
    def get_admin_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get admin audit log from Supabase"""
        try:
            result = self.supabase.table('admin_audit_log')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
            
        except Exception as e:
            print(f"❌ Error getting audit log: {str(e)}")
            return []
    
    # Utility methods
    def get_unique_ip_count(self) -> int:
        """Get count of unique IP addresses"""
        try:
            result = self.supabase.rpc('get_unique_ip_count').execute()
            return result.data if result.data else 0
        except:
            # Fallback method
            result = self.supabase.table('usage_logs').select('ip_address').execute()
            unique_ips = set(log['ip_address'] for log in result.data if log['ip_address'])
            return len(unique_ips)
    
    def get_recent_requests_count(self, hours: int = 24) -> int:
        """Get count of requests in the last N hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            result = self.supabase.table('usage_logs')\
                .select('id', count='exact')\
                .gte('timestamp', cutoff_time.isoformat())\
                .execute()
            
            return result.count
            
        except Exception as e:
            print(f"❌ Error getting recent requests count: {str(e)}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """Check Supabase database health and connectivity"""
        try:
            # Test connection
            result = self.supabase.table('usage_logs').select('id').limit(1).execute()
            
            return {
                "status": "healthy",
                "connection": "active",
                "database": "supabase_postgresql",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "connection": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global instance
supabase_db = None

def get_db():
    """Get or create Supabase database instance"""
    global supabase_db
    if supabase_db is None:
        supabase_db = SupabaseDB()
    return supabase_db
