# admin_dashboard.py - Admin Analytics Dashboard

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
import sqlite3
import json
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import secrets
import hashlib

load_dotenv()

# Admin credentials - these MUST be set in environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables!")

# Security
security = HTTPBasic()
templates = Jinja2Templates(directory="admin_templates")

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")
    
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class AnalyticsDB:
    def __init__(self, db_path="analytics.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                subject_length INTEGER,
                body_length INTEGER,
                overall_score INTEGER,
                ai_enhanced BOOLEAN,
                processing_time_ms INTEGER,
                error_occurred BOOLEAN DEFAULT FALSE,
                error_message TEXT
            )
        ''')
        
        # Daily statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                ai_enhanced_requests INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0,
                unique_ips INTEGER DEFAULT 0
            )
        ''')
        
        # API usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                api_provider TEXT,
                tokens_used INTEGER,
                cost_usd REAL,
                success BOOLEAN
            )
        ''')
        
        # Admin users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'admin',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Admin audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Email alert settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                threshold_value REAL,
                email_recipients TEXT,
                is_enabled BOOLEAN DEFAULT 1,
                created_by TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_request(self, ip: str, user_agent: str, subject_len: int, body_len: int, 
                   score: int, ai_enhanced: bool, processing_time: int, 
                   error: bool = False, error_msg: str = None):
        """Log a request to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO usage_logs 
            (ip_address, user_agent, subject_length, body_length, overall_score, 
             ai_enhanced, processing_time_ms, error_occurred, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip, user_agent, subject_len, body_len, score, ai_enhanced, 
              processing_time, error, error_msg))
        
        conn.commit()
        conn.close()
        
        # Update daily stats
        self.update_daily_stats()
    
    def update_daily_stats(self):
        """Update daily statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Get today's stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN error_occurred = 0 THEN 1 END) as successful,
                COUNT(CASE WHEN error_occurred = 1 THEN 1 END) as failed,
                COUNT(CASE WHEN ai_enhanced = 1 THEN 1 END) as ai_enhanced,
                AVG(CASE WHEN error_occurred = 0 THEN overall_score END) as avg_score,
                COUNT(DISTINCT ip_address) as unique_ips
            FROM usage_logs 
            WHERE DATE(timestamp) = ?
        ''', (today,))
        
        stats = cursor.fetchone()
        
        # Insert or update daily stats
        cursor.execute('''
            INSERT OR REPLACE INTO daily_stats 
            (date, total_requests, successful_requests, failed_requests, 
             ai_enhanced_requests, avg_score, unique_ips)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (today, stats[0], stats[1], stats[2], stats[3], 
              stats[4] or 0, stats[5]))
        
        conn.commit()
        conn.close()
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                COUNT(CASE WHEN error_occurred = 0 THEN 1 END) as successful_requests,
                COUNT(CASE WHEN ai_enhanced = 1 THEN 1 END) as ai_enhanced_requests,
                AVG(CASE WHEN error_occurred = 0 THEN overall_score END) as avg_score,
                COUNT(DISTINCT ip_address) as unique_users,
                AVG(processing_time_ms) as avg_processing_time
            FROM usage_logs 
            WHERE timestamp >= ?
        ''', (thirty_days_ago,))
        
        overall_stats = cursor.fetchone()
        
        # Daily stats for chart (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        cursor.execute('''
            SELECT date, total_requests, successful_requests, ai_enhanced_requests, avg_score
            FROM daily_stats 
            WHERE date >= ?
            ORDER BY date
        ''', (seven_days_ago.date(),))
        
        daily_stats = cursor.fetchall()
        
        # Top error messages
        cursor.execute('''
            SELECT error_message, COUNT(*) as count
            FROM usage_logs 
            WHERE error_occurred = 1 AND error_message IS NOT NULL
            AND timestamp >= ?
            GROUP BY error_message
            ORDER BY count DESC
            LIMIT 5
        ''', (thirty_days_ago,))
        
        top_errors = cursor.fetchall()
        
        # Usage by hour (today)
        today = datetime.now().date()
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as requests
            FROM usage_logs 
            WHERE DATE(timestamp) = ?
            GROUP BY hour
            ORDER BY hour
        ''', (today,))
        
        hourly_usage = cursor.fetchall()
        
        conn.close()
        
        return {
            'overall_stats': {
                'total_requests': overall_stats[0] or 0,
                'successful_requests': overall_stats[1] or 0,
                'ai_enhanced_requests': overall_stats[2] or 0,
                'avg_score': round(overall_stats[3] or 0, 1),
                'unique_users': overall_stats[4] or 0,
                'avg_processing_time': round(overall_stats[5] or 0, 1),
                'success_rate': round((overall_stats[1] or 0) / max(overall_stats[0] or 1, 1) * 100, 1)
            },
            'daily_stats': [
                {
                    'date': stat[0],
                    'total_requests': stat[1],
                    'successful_requests': stat[2],
                    'ai_enhanced_requests': stat[3],
                    'avg_score': round(stat[4] or 0, 1)
                } for stat in daily_stats
            ],
            'top_errors': [
                {'error': error[0], 'count': error[1]} for error in top_errors
            ],
            'hourly_usage': [
                {'hour': f"{int(hour[0]):02d}:00", 'requests': hour[1]} 
                for hour in hourly_usage
            ]
        }
    
    def get_usage_logs(self, limit: int = 1000) -> List[Dict]:
        """Get usage logs for export"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, ip_address, user_agent, subject_length, body_length, 
                   overall_score, ai_enhanced, processing_time_ms, error_occurred, error_message
            FROM usage_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': log[0],
                'ip': log[1],
                'user_agent': log[2],
                'subject_len': log[3],
                'body_len': log[4],
                'score': log[5],
                'ai_enhanced': bool(log[6]),
                'processing_time': log[7],
                'error': bool(log[8]),
                'error_msg': log[9]
            } for log in logs
        ]
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Count records to be deleted
        cursor.execute('SELECT COUNT(*) FROM usage_logs WHERE timestamp < ?', (cutoff_date,))
        count_to_delete = cursor.fetchone()[0]
        
        # Delete old usage logs
        cursor.execute('DELETE FROM usage_logs WHERE timestamp < ?', (cutoff_date,))
        
        # Delete old daily stats
        cursor.execute('DELETE FROM daily_stats WHERE date < ?', (cutoff_date.date(),))
        
        # Delete old API usage logs
        cursor.execute('DELETE FROM api_usage WHERE timestamp < ?', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        return count_to_delete
    
    def create_admin_user(self, username: str, password: str, email: str = None, role: str = "admin") -> bool:
        """Create a new admin user"""
        import hashlib
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO admin_users (username, password_hash, email, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, email, role))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Username already exists
    
    def verify_admin_user(self, username: str, password: str) -> Dict:
        """Verify admin credentials and return user info"""
        import hashlib
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT username, email, role, last_login, is_active
            FROM admin_users 
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE admin_users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE username = ?
            ''', (username,))
            conn.commit()
            
            conn.close()
            return {
                'username': user[0],
                'email': user[1],
                'role': user[2],
                'last_login': user[3],
                'is_active': bool(user[4])
            }
        
        conn.close()
        return None
    
    def log_admin_action(self, username: str, action: str, details: str = None, ip_address: str = None):
        """Log admin actions for audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_audit_log (admin_username, action, details, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (username, action, details, ip_address))
        
        conn.commit()
        conn.close()
    
    def get_admin_users(self) -> List[Dict]:
        """Get all admin users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, role, created_at, last_login, is_active
            FROM admin_users
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'username': user[0],
                'email': user[1],
                'role': user[2],
                'created_at': user[3],
                'last_login': user[4],
                'is_active': bool(user[5])
            } for user in users
        ]
    
    def get_advanced_analytics(self, start_date: str = None, end_date: str = None, 
                             ip_filter: str = None, score_min: int = None, score_max: int = None) -> Dict:
        """Get advanced analytics with filtering"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build WHERE clause based on filters
        where_conditions = []
        params = []
        
        if start_date:
            where_conditions.append("DATE(timestamp) >= ?")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("DATE(timestamp) <= ?")
            params.append(end_date)
        
        if ip_filter:
            where_conditions.append("ip_address LIKE ?")
            params.append(f"%{ip_filter}%")
        
        if score_min is not None:
            where_conditions.append("overall_score >= ?")
            params.append(score_min)
        
        if score_max is not None:
            where_conditions.append("overall_score <= ?")
            params.append(score_max)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get filtered analytics
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_requests,
                AVG(overall_score) as avg_score,
                MIN(overall_score) as min_score,
                MAX(overall_score) as max_score,
                AVG(processing_time_ms) as avg_processing_time,
                COUNT(DISTINCT ip_address) as unique_ips,
                SUM(CASE WHEN ai_enhanced = 1 THEN 1 ELSE 0 END) as ai_enhanced_count,
                SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as error_count
            FROM usage_logs {where_clause}
        ''', params)
        
        stats = cursor.fetchone()
        
        # Get hourly distribution
        cursor.execute(f'''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as requests,
                AVG(overall_score) as avg_score
            FROM usage_logs {where_clause}
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        ''', params)
        
        hourly_data = cursor.fetchall()
        
        # Get score distribution
        cursor.execute(f'''
            SELECT 
                CASE 
                    WHEN overall_score >= 80 THEN 'Excellent (80-100)'
                    WHEN overall_score >= 60 THEN 'Good (60-79)'
                    WHEN overall_score >= 40 THEN 'Fair (40-59)'
                    ELSE 'Poor (0-39)'
                END as score_range,
                COUNT(*) as count
            FROM usage_logs {where_clause}
            GROUP BY score_range
        ''', params)
        
        score_distribution = cursor.fetchall()
        
        conn.close()
        
        return {
            'filtered_stats': {
                'total_requests': stats[0] or 0,
                'avg_score': round(stats[1] or 0, 2),
                'min_score': stats[2] or 0,
                'max_score': stats[3] or 0,
                'avg_processing_time': round(stats[4] or 0, 2),
                'unique_ips': stats[5] or 0,
                'ai_enhanced_count': stats[6] or 0,
                'error_count': stats[7] or 0
            },
            'hourly_distribution': [
                {'hour': f"{int(hour[0]):02d}:00", 'requests': hour[1], 'avg_score': round(hour[2] or 0, 1)}
                for hour in hourly_data
            ],
            'score_distribution': [
                {'range': dist[0], 'count': dist[1]}
                for dist in score_distribution
            ]
        }

# Initialize analytics database
analytics_db = AnalyticsDB()

class HuggingFaceMonitor:
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = "https://api-inference.huggingface.co"
    
    def get_api_usage(self) -> Dict:
        """Get Hugging Face API usage information"""
        if not self.api_key:
            return {"error": "No API key configured"}
        
        try:
            # Check account info (this endpoint may not exist, but we'll try)
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # For now, return estimated usage based on our logs
            # In a real implementation, you'd integrate with HF's billing API if available
            conn = sqlite3.connect(analytics_db.db_path)
            cursor = conn.cursor()
            
            # Count AI requests in the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute('''
                SELECT COUNT(*) FROM usage_logs 
                WHERE ai_enhanced = 1 AND timestamp >= ?
            ''', (thirty_days_ago,))
            
            requests_last_30_days = cursor.fetchone()[0]
            conn.close()
            
            # Estimate tokens (rough calculation)
            estimated_tokens_per_request = 50  # Average tokens per email analysis
            estimated_tokens_used = requests_last_30_days * estimated_tokens_per_request
            
            return {
                'api_key_active': True,
                'requests_last_30_days': requests_last_30_days,
                'estimated_tokens_used': estimated_tokens_used,
                'monthly_limit': 30000,  # Free tier limit
                'estimated_remaining': max(0, 30000 - estimated_tokens_used),
                'usage_percentage': min(100, (estimated_tokens_used / 30000) * 100)
            }
            
        except Exception as e:
            return {"error": f"Failed to check API usage: {str(e)}"}

hf_monitor = HuggingFaceMonitor()

def create_admin_app():
    """Create the admin FastAPI app"""
    app = FastAPI(title="InboxQualify Admin Dashboard")
    
    @app.get("/", response_class=HTMLResponse)
    async def admin_dashboard(request: Request, admin: str = Depends(verify_admin)):
        """Main admin dashboard"""
        dashboard_data = analytics_db.get_dashboard_data()
        api_usage = hf_monitor.get_api_usage()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "dashboard_data": dashboard_data,
            "api_usage": api_usage,
            "admin_user": admin
        })
    
    @app.get("/api/stats")
    async def get_stats(admin: str = Depends(verify_admin)):
        """API endpoint for real-time stats"""
        return {
            "dashboard_data": analytics_db.get_dashboard_data(),
            "api_usage": hf_monitor.get_api_usage(),
            "timestamp": datetime.now().isoformat()
        }
    
    return app

# Export the analytics database for use in main app
__all__ = ['analytics_db', 'create_admin_app']
