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
import uuid

# Load environment variables
load_dotenv()

class SupabaseDB:
    def __init__(self):
        """Initialize Supabase client with configuration from environment variables"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for admin operations
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        
        # Create Supabase client with SSL error handling
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        except Exception as e:
            print(f"⚠️ Supabase client creation warning: {e}")
            # Still create client, but with awareness of potential SSL issues
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize database schema on first connection
        self.initialize_database()
    
    def _execute_with_retry(self, operation, max_retries=2):
        """Execute Supabase operation with retry logic for SSL errors"""
        import time
        import ssl
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for SSL-related errors
                if any(ssl_error in error_str for ssl_error in [
                    'ssl', 'sslv3_alert_bad_record_mac', 'certificate', 'handshake'
                ]):
                    if attempt < max_retries:
                        print(f"🔄 SSL error on attempt {attempt + 1}, retrying in {attempt + 1}s...")
                        time.sleep(attempt + 1)  # Progressive backoff
                        continue
                    else:
                        print(f"❌ SSL error after {max_retries + 1} attempts: {e}")
                        return None
                else:
                    # Non-SSL error, don't retry
                    raise e
        
        return None
    
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
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("Fetching usage statistics from Supabase")
            
            # Total requests with retry logic for SSL issues
            total_result = self._execute_with_retry(
                lambda: self.supabase.table('usage_logs').select('id', count='exact').execute()
            )
            total_requests = total_result.count if total_result else 0
            
            # Today's requests
            today = datetime.now().date()
            today_result = self._execute_with_retry(
                lambda: self.supabase.table('usage_logs')\
                    .select('id', count='exact')\
                    .gte('timestamp', today.isoformat())\
                    .execute()
            )
            today_requests = today_result.count if today_result else 0
            
            # Average score
            avg_result = self._execute_with_retry(
                lambda: self.supabase.rpc('get_average_score').execute()
            )
            avg_score = avg_result.data if avg_result and avg_result.data else 0
            
            # Error rate
            error_result = self._execute_with_retry(
                lambda: self.supabase.table('usage_logs')\
                    .select('id', count='exact')\
                    .not_.is_('error_message', 'null')\
                    .execute()
            )
            error_count = error_result.count if error_result else 0
            
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            logger.info(f"Successfully retrieved stats: {total_requests} total requests")
            
            return {
                "total_requests": total_requests,
                "today_requests": today_requests,
                "average_score": round(avg_score, 2),
                "error_rate": round(error_rate, 2),
                "unique_ips": self.get_unique_ip_count(),
                "last_24h_requests": self.get_recent_requests_count(24)
            }
            
        except Exception as e:
            error_str = str(e).lower()
            if 'ssl' in error_str or 'certificate' in error_str:
                print(f"❌ SSL connection error: {str(e)}")
                # Return proper error state instead of fake data
                return {
                    "total_requests": 0,
                    "today_requests": 0,
                    "average_score": 0,
                    "error_rate": 0,
                    "unique_ips": 0,
                    "last_24h_requests": 0,
                    "status": "connection_error",
                    "message": "Database connection temporarily unavailable"
                }
            else:
                print(f"❌ Error getting usage stats: {str(e)}")
                return {
                    "total_requests": 0,
                    "today_requests": 0,
                    "average_score": 0,
                    "error_rate": 0,
                    "unique_ips": 0,
                    "last_24h_requests": 0,
                    "status": "error",
                    "message": "Unable to retrieve statistics"
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
    
    def get_advanced_analytics(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                             ip_filter: Optional[str] = None, min_score: Optional[int] = None, 
                             max_score: Optional[int] = None) -> Dict[str, Any]:
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
                return {
                    "filtered_requests": 0,
                    "filtered_stats": {
                        "total_requests": 0,
                        "min_score": 0,
                        "max_score": 0,
                        "avg_score": 0,
                        "unique_ips": 0,
                        "error_count": 0
                    },
                    "score_stats": {},
                    "hourly_data": [],
                    "unique_ips": 0,
                    "error_count": 0,
                    "score_distribution": []
                }
            
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
            
            # Score distribution for chart
            score_distribution = []
            if scores:
                ranges = [
                    {"range": "0-20", "count": len([s for s in scores if 0 <= s <= 20])},
                    {"range": "21-40", "count": len([s for s in scores if 21 <= s <= 40])},
                    {"range": "41-60", "count": len([s for s in scores if 41 <= s <= 60])},
                    {"range": "61-80", "count": len([s for s in scores if 61 <= s <= 80])},
                    {"range": "81-100", "count": len([s for s in scores if 81 <= s <= 100])},
                ]
                score_distribution = [r for r in ranges if r["count"] > 0]
            
            return {
                "filtered_requests": len(logs),
                "filtered_stats": {
                    "total_requests": len(logs),
                    "min_score": min(scores) if scores else 0,
                    "max_score": max(scores) if scores else 0,
                    "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
                    "unique_ips": len(set(log['ip_address'] for log in logs if log['ip_address'])),
                    "error_count": len([log for log in logs if log['error_message']])
                },
                "score_stats": score_stats,
                "hourly_data": hourly_list,
                "unique_ips": len(set(log['ip_address'] for log in logs if log['ip_address'])),
                "error_count": len([log for log in logs if log['error_message']]),
                "score_distribution": score_distribution
            }
            
        except Exception as e:
            print(f"❌ Error getting advanced analytics: {str(e)}")
            return {
                "filtered_requests": 0, 
                "filtered_stats": {
                    "total_requests": 0,
                    "min_score": 0,
                    "max_score": 0,
                    "avg_score": 0,
                    "unique_ips": 0,
                    "error_count": 0
                },
                "score_stats": {}, 
                "hourly_data": [],
                "unique_ips": 0,
                "error_count": 0,
                "score_distribution": []
            }
    
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
    
    def log_admin_action(self, admin_username: str, action: str, details: Optional[str] = None, ip_address: Optional[str] = None):
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
        
    # In your supabase_db.py file, inside the SupabaseDB class:

    def get_user_by_email(self, email: str):
        """
        Fetches a single user from the 'users' table by their email.
        """
        try:
            # Query the 'users' table where the 'email' column matches
            response = self.supabase.table('users').select('*').eq('email', email).execute()
            
            # The result is a list, so if it's not empty, return the first item (the user)
            if response.data:
                return response.data[0]
            
            # If no user is found, return None
            return None
        except Exception as e:
            print(f"ERROR: Could not fetch user by email '{email}': {e}")
            return None

    def create_user(self, email: str, hashed_password: str):
        """
        Inserts a new user into the 'users' table.
        """
        try:
            # Insert the new user data into the 'users' table
            response = self.supabase.table('users').insert({
                'email': email,
                'password_hash': hashed_password,
                'subscription_plan': 'free' # Default plan on signup
            }).execute()

            # If the insertion was successful, return the new user's data
            if response.data:
                return response.data[0]
                
            return None
        except Exception as e:
            print(f"ERROR: Could not create user '{email}': {e}")
            return None

    # --- Campaign & Batch Methods ---
    
    def create_campaign(self, name: str, description: str = "") -> str:
        """Create a new campaign"""
        try:
            data = {
                "name": name,
                "description": description
            }
            result = self.supabase.table('campaigns').insert(data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Error creating campaign: {str(e)}")
            return None

    def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign details"""
        try:
            result = self.supabase.table('campaigns').select('*').eq('id', campaign_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Error getting campaign: {str(e)}")
            return None

    def list_campaigns(self) -> List[Dict[str, Any]]:
        """List all campaigns"""
        try:
            result = self.supabase.table('campaigns').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Error listing campaigns: {str(e)}")
            return []

    def create_batch(self, campaign_id: Optional[str], summary: Dict[str, Any], filename: str = None) -> str:
        """Create a new batch record"""
        try:
            # Generate a UUID if not provided (though Supabase would do it, we might need it for items)
            batch_id = str(uuid.uuid4())
            
            data = {
                "id": batch_id,
                "campaign_id": campaign_id,
                "summary": json.dumps(summary) if isinstance(summary, dict) else summary,
                "original_filename": filename
            }
            
            result = self.supabase.table('batches').insert(data).execute()
            return result.data[0]['id'] if result.data else batch_id
        except Exception as e:
            print(f"❌ Error creating batch: {str(e)}")
            return None

    def add_batch_items(self, batch_id: str, items: List[Dict[str, Any]]) -> bool:
        """Add multiple items to a batch"""
        try:
            # Prepare items for insertion
            db_items = []
            for item in items:
                db_items.append({
                    "batch_id": batch_id,
                    "email_data": json.dumps({
                        "subject": item.get("subject"),
                        "body": item.get("body"),
                        "sender_name": item.get("sender_name"),
                        "sender_email": item.get("sender_email"),
                        "company": item.get("company"),
                        "industry": item.get("industry")
                    }),
                    "analysis_result": json.dumps({
                        "score": item.get("score"),
                        "suggestions": item.get("suggestions"),
                        "word_count": item.get("word_count"),
                        "subject_length": item.get("subject_length"),
                        "priority_issues": item.get("priority_issues"),
                        "rewrite": item.get("rewrite")
                    })
                })
            
            # Insert in chunks to avoid payload limits
            chunk_size = 100
            for i in range(0, len(db_items), chunk_size):
                chunk = db_items[i:i + chunk_size]
                self.supabase.table('batch_items').insert(chunk).execute()
                
            return True
        except Exception as e:
            print(f"❌ Error adding batch items: {str(e)}")
            return False

    def get_batch(self, batch_id: str) -> Dict[str, Any]:
        """Get batch details with items"""
        try:
            # Get batch info
            batch_result = self.supabase.table('batches').select('*').eq('id', batch_id).execute()
            if not batch_result.data:
                return None
            
            batch = batch_result.data[0]
            
            # Get items
            items_result = self.supabase.table('batch_items').select('*').eq('batch_id', batch_id).execute()
            
            # Reconstruct the format expected by the frontend
            results = []
            for item in items_result.data:
                email_data = item.get('email_data', {}) or {}
                analysis = item.get('analysis_result', {}) or {}
                
                # Handle string vs dict if Supabase returns JSON as dict automatically (it usually does)
                if isinstance(email_data, str): email_data = json.loads(email_data)
                if isinstance(analysis, str): analysis = json.loads(analysis)
                
                results.append({
                    "id": item['id'],
                    "subject": email_data.get('subject'),
                    "body": email_data.get('body'),
                    "sender_name": email_data.get('sender_name'),
                    "sender_email": email_data.get('sender_email'),
                    "company": email_data.get('company'),
                    "industry": email_data.get('industry'),
                    "score": analysis.get('score'),
                    "suggestions": analysis.get('suggestions', []),
                    "word_count": analysis.get('word_count'),
                    "subject_length": analysis.get('subject_length'),
                    "priority_issues": analysis.get('priority_issues', []),
                    "suggestion_count": len(analysis.get('suggestions', [])),
                    "rewrite": analysis.get('rewrite')
                })
            
            return {
                "batch_id": batch['id'],
                "timestamp": batch['created_at'],
                "summary": batch['summary'] if isinstance(batch['summary'], dict) else json.loads(batch['summary']),
                "results": results,
                "campaign_id": batch['campaign_id']
            }
        except Exception as e:
            print(f"❌ Error getting batch: {str(e)}")
            return None

    def get_campaign_batches(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get all batches for a campaign"""
        try:
            result = self.supabase.table('batches').select('*').eq('campaign_id', campaign_id).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Error getting campaign batches: {str(e)}")
            return []

    # --- System Settings Methods ---

    def get_system_settings(self, key: str) -> Dict[str, Any]:
        """Get system settings by key"""
        try:
            result = self.supabase.table('system_settings').select('value').eq('key', key).execute()
            if result.data:
                return result.data[0]['value']
            return None
        except Exception as e:
            print(f"❌ Error getting system settings: {str(e)}")
            return None

    def update_system_settings(self, key: str, value: Dict[str, Any]) -> bool:
        """Update system settings"""
        try:
            data = {
                "key": key,
                "value": json.dumps(value) if isinstance(value, dict) else value,
                "updated_at": datetime.now().isoformat()
            }
            # Upsert
            self.supabase.table('system_settings').upsert(data).execute()
            return True
        except Exception as e:
            print(f"❌ Error updating system settings: {str(e)}")
            return False

# Global instance
supabase_db = None

def get_db():
    """Get or create Supabase database instance"""
    global supabase_db
    if supabase_db is None:
        supabase_db = SupabaseDB()
    return supabase_db
