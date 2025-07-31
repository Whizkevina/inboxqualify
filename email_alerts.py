"""
Email Alert System for InboxQualify Admin Dashboard
Sends notifications for system events and threshold breaches
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class EmailAlertSystem:
    def __init__(self, analytics_db):
        self.analytics_db = analytics_db
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("ALERT_FROM_EMAIL", self.smtp_username)
        
    def send_email(self, to_emails: List[str], subject: str, html_content: str, text_content: str = None):
        """Send email alert"""
        if not self.smtp_username or not self.smtp_password:
            print("⚠️ Email credentials not configured. Skipping email alert.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add text version
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            for email in to_emails:
                server.sendmail(self.from_email, email, msg.as_string())
            
            server.quit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def check_error_rate_alert(self):
        """Check if error rate exceeds threshold"""
        conn = sqlite3.connect(self.analytics_db.db_path)
        cursor = conn.cursor()
        
        # Check error rate in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN error_occurred = 1 THEN 1 ELSE 0 END) as error_count
            FROM usage_logs 
            WHERE timestamp >= ?
        ''', (one_hour_ago,))
        
        result = cursor.fetchone()
        total_requests = result[0] or 0
        error_count = result[1] or 0
        
        if total_requests > 0:
            error_rate = (error_count / total_requests) * 100
            
            # Check if error rate exceeds 10%
            if error_rate > 10 and total_requests >= 5:  # At least 5 requests
                self._send_error_rate_alert(error_rate, error_count, total_requests)
        
        conn.close()
    
    def check_high_usage_alert(self):
        """Check if usage is unusually high"""
        conn = sqlite3.connect(self.analytics_db.db_path)
        cursor = conn.cursor()
        
        # Check requests in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute('''
            SELECT COUNT(*) FROM usage_logs 
            WHERE timestamp >= ?
        ''', (one_hour_ago,))
        
        requests_last_hour = cursor.fetchone()[0] or 0
        
        # Get average requests per hour for last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        cursor.execute('''
            SELECT 
                COUNT(*) / (24 * 7) as avg_requests_per_hour
            FROM usage_logs 
            WHERE timestamp >= ?
        ''', (seven_days_ago,))
        
        avg_requests = cursor.fetchone()[0] or 0
        
        # Alert if current hour is 3x higher than average
        if avg_requests > 0 and requests_last_hour > (avg_requests * 3) and requests_last_hour > 50:
            self._send_high_usage_alert(requests_last_hour, avg_requests)
        
        conn.close()
    
    def check_api_failure_alert(self):
        """Check for API failures"""
        conn = sqlite3.connect(self.analytics_db.db_path)
        cursor = conn.cursor()
        
        # Check for consecutive AI failures
        cursor.execute('''
            SELECT ai_enhanced, error_occurred, timestamp
            FROM usage_logs 
            WHERE timestamp >= datetime('now', '-30 minutes')
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        recent_requests = cursor.fetchall()
        
        # Count consecutive AI failures
        consecutive_failures = 0
        for request in recent_requests:
            if request[0] == 1 and request[1] == 1:  # AI enhanced but failed
                consecutive_failures += 1
            else:
                break
        
        if consecutive_failures >= 5:
            self._send_api_failure_alert(consecutive_failures)
        
        conn.close()
    
    def _send_error_rate_alert(self, error_rate: float, error_count: int, total_requests: int):
        """Send error rate alert"""
        subject = f"🚨 InboxQualify: High Error Rate Alert ({error_rate:.1f}%)"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #dc3545;">🚨 High Error Rate Alert</h2>
                <p><strong>Your InboxQualify service is experiencing a high error rate.</strong></p>
                
                <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h3>Alert Details:</h3>
                    <ul>
                        <li><strong>Error Rate:</strong> {error_rate:.1f}%</li>
                        <li><strong>Failed Requests:</strong> {error_count}</li>
                        <li><strong>Total Requests (last hour):</strong> {total_requests}</li>
                        <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    </ul>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107;">
                    <h4>Recommended Actions:</h4>
                    <ol>
                        <li>Check the admin dashboard for detailed error logs</li>
                        <li>Verify Hugging Face API status and quota</li>
                        <li>Review recent system changes</li>
                        <li>Monitor for continued issues</li>
                    </ol>
                </div>
                
                <p style="margin-top: 20px;">
                    <a href="http://localhost:8000/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Admin Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        # Get alert recipients
        recipients = self._get_alert_recipients('error_rate')
        if recipients:
            self.send_email(recipients, subject, html_content)
    
    def _send_high_usage_alert(self, current_requests: int, avg_requests: float):
        """Send high usage alert"""
        subject = f"📈 InboxQualify: High Usage Alert ({current_requests} requests/hour)"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #28a745;">📈 High Usage Alert</h2>
                <p><strong>Your InboxQualify service is experiencing unusually high usage.</strong></p>
                
                <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h3>Usage Statistics:</h3>
                    <ul>
                        <li><strong>Current Hour:</strong> {current_requests} requests</li>
                        <li><strong>7-Day Average:</strong> {avg_requests:.1f} requests/hour</li>
                        <li><strong>Increase Factor:</strong> {current_requests/avg_requests:.1f}x</li>
                        <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    </ul>
                </div>
                
                <div style="background: #d1ecf1; padding: 15px; border-radius: 6px; border-left: 4px solid #17a2b8;">
                    <h4>This could indicate:</h4>
                    <ul>
                        <li>Increased customer usage (good news!)</li>
                        <li>Marketing campaign success</li>
                        <li>Potential automated/bot traffic</li>
                        <li>System integration by a customer</li>
                    </ul>
                </div>
                
                <p style="margin-top: 20px;">
                    <a href="http://localhost:8000/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Admin Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        recipients = self._get_alert_recipients('high_usage')
        if recipients:
            self.send_email(recipients, subject, html_content)
    
    def _send_api_failure_alert(self, consecutive_failures: int):
        """Send API failure alert"""
        subject = f"⚠️ InboxQualify: AI API Failure Alert ({consecutive_failures} consecutive failures)"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #ffc107;">⚠️ AI API Failure Alert</h2>
                <p><strong>The Hugging Face AI API is experiencing consecutive failures.</strong></p>
                
                <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h3>Failure Details:</h3>
                    <ul>
                        <li><strong>Consecutive Failures:</strong> {consecutive_failures}</li>
                        <li><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li><strong>Impact:</strong> Falling back to local analysis</li>
                    </ul>
                </div>
                
                <div style="background: #f8d7da; padding: 15px; border-radius: 6px; border-left: 4px solid #dc3545;">
                    <h4>Immediate Actions Required:</h4>
                    <ol>
                        <li>Check Hugging Face API status</li>
                        <li>Verify API key and quotas</li>
                        <li>Review API usage limits</li>
                        <li>Consider switching models if needed</li>
                    </ol>
                </div>
                
                <p style="margin-top: 20px;">
                    <a href="http://localhost:8000/admin" 
                       style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        View Admin Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        recipients = self._get_alert_recipients('api_failure')
        if recipients:
            self.send_email(recipients, subject, html_content)
    
    def _get_alert_recipients(self, alert_type: str) -> List[str]:
        """Get email recipients for specific alert type"""
        # For now, return admin email from environment
        admin_email = os.getenv("ADMIN_EMAIL")
        if admin_email:
            return [admin_email]
        return []
    
    def run_all_checks(self):
        """Run all alert checks"""
        print("🔍 Running email alert checks...")
        self.check_error_rate_alert()
        self.check_high_usage_alert()
        self.check_api_failure_alert()
        print("✅ Email alert checks completed")

# Initialize email alert system
def create_email_alert_system(analytics_db):
    return EmailAlertSystem(analytics_db)
