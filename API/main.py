# main.py - FINAL VERSION with Admin Analytics

# 1. Import necessary libraries
import os
import sys
import json
import time
import secrets
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_analyzer import LocalEmailAnalyzer
from huggingface_analyzer import HuggingFaceAnalyzer

# Load environment variables from .env file
load_dotenv()

# Initialize security
security = HTTPBasic()

# Import admin dashboard (will be created)
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from admin_dashboard import AnalyticsDB, HuggingFaceMonitor
    from email_alerts import create_email_alert_system
    analytics_db = AnalyticsDB()
    hf_monitor = HuggingFaceMonitor()
    email_alerts = create_email_alert_system(analytics_db)
    ADMIN_ENABLED = True
    print("✅ Admin dashboard initialized successfully")
    print("✅ Email alert system initialized")
except ImportError as e:
    print(f"Admin dashboard not available - running without analytics: {e}")
    analytics_db = None
    hf_monitor = None
    email_alerts = None
    ADMIN_ENABLED = False

# --- API KEY CONFIGURATION ---
# Load API keys from environment variables
try:
    # Try Hugging Face first (our new primary AI)
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_api_key:
        print("Warning: HUGGINGFACE_API_KEY not set. Will use local analyzer only.")
    else:
        print("Hugging Face API key loaded successfully!")
    
except Exception as e:
    print(f"Error loading API keys: {e}")
    print("Will use local analyzer as fallback.")

# --- App Setup & CORS ---
origins = ["*"] # Allows all origins for local development
app = FastAPI(
    title="InboxQualify API",
    description="AI-powered cold email analysis and scoring",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and admin
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files (CSS, JS, images)
try:
    app.mount("/css", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "js")), name="js")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

# Mount admin app if available
if ADMIN_ENABLED:
    try:
        from fastapi.templating import Jinja2Templates
        
        # Set up templates directory
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "admin_templates")
        templates = Jinja2Templates(directory=templates_dir)
        
        @app.get("/admin", response_class=HTMLResponse)
        async def admin_dashboard(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
            """Admin dashboard endpoint"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid admin credentials",
                    headers={"WWW-Authenticate": "Basic"},
                )
            
            # Get dashboard data if analytics is available
            dashboard_data = {}
            api_usage = {}
            
            if analytics_db:
                try:
                    dashboard_data = analytics_db.get_dashboard_data()
                except Exception as e:
                    print(f"Error getting dashboard data: {e}")
                    dashboard_data = {"error": "Analytics unavailable"}
            
            if hf_monitor:
                try:
                    api_usage = hf_monitor.get_api_usage()
                except Exception as e:
                    print(f"Error getting API usage: {e}")
                    api_usage = {"error": "API monitoring unavailable"}
            
            return templates.TemplateResponse("dashboard_phase2.html", {
                "request": request,
                "dashboard_data": dashboard_data,
                "api_usage": api_usage,
                "admin_user": credentials.username
            })

        @app.get("/admin/export")
        async def export_analytics(format: str = "csv", credentials: HTTPBasicCredentials = Depends(security)):
            """Export analytics data"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            try:
                import csv
                import io
                from datetime import datetime
                
                # Get all usage logs
                logs = analytics_db.get_usage_logs(limit=10000)  # Get up to 10k records
                
                if format.lower() == "csv":
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # Write header
                    writer.writerow(['Timestamp', 'IP', 'User Agent', 'Subject Length', 'Body Length', 
                                   'Score', 'AI Enhanced', 'Processing Time (ms)', 'Error', 'Error Message'])
                    
                    # Write data
                    for log in logs:
                        writer.writerow([
                            log.get('timestamp', ''),
                            log.get('ip', ''),
                            log.get('user_agent', ''),
                            log.get('subject_len', 0),
                            log.get('body_len', 0),
                            log.get('score', 0),
                            log.get('ai_enhanced', False),
                            log.get('processing_time', 0),
                            log.get('error', False),
                            log.get('error_msg', '')
                        ])
                    
                    content = output.getvalue()
                    output.close()
                    
                    from fastapi.responses import Response
                    return Response(
                        content=content,
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=inboxqualify_data_{datetime.now().strftime('%Y%m%d')}.csv"}
                    )
                
                elif format.lower() == "json":
                    import json
                    from fastapi.responses import Response
                    
                    data = {
                        "export_date": datetime.now().isoformat(),
                        "total_records": len(logs),
                        "usage_logs": logs
                    }
                    
                    return Response(
                        content=json.dumps(data, indent=2),
                        media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename=inboxqualify_data_{datetime.now().strftime('%Y%m%d')}.json"}
                    )
                
                else:
                    raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'json'")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

        @app.post("/admin/cleanup")
        async def cleanup_old_data(credentials: HTTPBasicCredentials = Depends(security)):
            """Clean up data older than 30 days"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            try:
                deleted_count = analytics_db.cleanup_old_data(days=30)
                return {"message": f"Successfully deleted {deleted_count} old records", "deleted_count": deleted_count}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

        @app.get("/admin/settings")
        async def get_admin_settings(credentials: HTTPBasicCredentials = Depends(security)):
            """Get admin settings"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            return {
                "huggingface_api_enabled": bool(os.getenv("HUGGINGFACE_API_KEY")),
                "analytics_enabled": ADMIN_ENABLED,
                "admin_username": os.getenv("ADMIN_USERNAME", "admin"),
                "auto_cleanup_enabled": True,  # Could be configurable
                "max_requests_per_hour": 1000  # Could be configurable
            }

        @app.post("/admin/settings")
        async def update_admin_settings(settings: dict, credentials: HTTPBasicCredentials = Depends(security)):
            """Update admin settings"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            # This is a simplified version - in production, you'd want proper settings management
            return {"message": "Settings updated successfully", "updated_settings": settings}

        # === PHASE 2 ENHANCEMENTS ===
        
        @app.get("/admin/analytics/advanced")
        async def get_advanced_analytics(
            start_date: str = None, 
            end_date: str = None,
            ip_filter: str = None,
            score_min: int = None,
            score_max: int = None,
            credentials: HTTPBasicCredentials = Depends(security)
        ):
            """Get advanced analytics with filtering"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            try:
                # Log admin action
                client_ip = "unknown"
                analytics_db.log_admin_action(
                    credentials.username, 
                    "advanced_analytics_view", 
                    f"Filters: date={start_date}-{end_date}, ip={ip_filter}, score={score_min}-{score_max}",
                    client_ip
                )
                
                return analytics_db.get_advanced_analytics(start_date, end_date, ip_filter, score_min, score_max)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")

        @app.get("/admin/users")
        async def get_admin_users(credentials: HTTPBasicCredentials = Depends(security)):
            """Get all admin users"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            # Log admin action
            analytics_db.log_admin_action(credentials.username, "view_admin_users", ip_address="unknown")
            
            return {"admin_users": analytics_db.get_admin_users()}

        @app.post("/admin/users")
        async def create_admin_user(user_data: dict, credentials: HTTPBasicCredentials = Depends(security)):
            """Create new admin user"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            # Validate required fields
            if not user_data.get("username") or not user_data.get("password"):
                raise HTTPException(status_code=400, detail="Username and password are required")
            
            # Create user
            success = analytics_db.create_admin_user(
                user_data["username"],
                user_data["password"],
                user_data.get("email"),
                user_data.get("role", "admin")
            )
            
            if success:
                # Log admin action
                analytics_db.log_admin_action(
                    credentials.username, 
                    "create_admin_user", 
                    f"Created user: {user_data['username']}",
                    "unknown"
                )
                return {"message": "Admin user created successfully", "username": user_data["username"]}
            else:
                raise HTTPException(status_code=400, detail="Username already exists")

        @app.post("/admin/alerts/test")
        async def test_email_alerts(credentials: HTTPBasicCredentials = Depends(security)):
            """Test email alert system"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not email_alerts:
                raise HTTPException(status_code=503, detail="Email alerts not available")
            
            # Log admin action
            analytics_db.log_admin_action(credentials.username, "test_email_alerts", ip_address="unknown")
            
            # Run alert checks
            try:
                email_alerts.run_all_checks()
                return {"message": "Email alert tests completed. Check logs for results."}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Alert test failed: {str(e)}")

        @app.get("/admin/audit-log")
        async def get_audit_log(limit: int = 100, credentials: HTTPBasicCredentials = Depends(security)):
            """Get admin audit log"""
            # Verify credentials
            correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
            correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
            if not (correct_username and correct_password):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
            
            if not analytics_db:
                raise HTTPException(status_code=503, detail="Analytics database not available")
            
            # Get audit log
            conn = analytics_db.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT admin_username, action, details, ip_address, timestamp
                FROM admin_audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            logs = cursor.fetchall()
            conn.close()
            
            return {
                "audit_logs": [
                    {
                        "username": log[0],
                        "action": log[1],
                        "details": log[2],
                        "ip_address": log[3],
                        "timestamp": log[4]
                    } for log in logs
                ]
            }
        
        print("Admin dashboard available at /admin")
    except Exception as e:
        print(f"Warning: Could not set up admin dashboard: {e}")
        ADMIN_ENABLED = False

# --- Pydantic Data Models ---
class EmailInput(BaseModel):
    subject: str
    email_body: str

class CategoryResult(BaseModel):
    name: str
    score: int
    maxScore: int
    feedback: str

class AnalysisResult(BaseModel):
    overallScore: int
    verdict: str
    breakdown: list[CategoryResult]


# --- AI Analysis Function ---

async def analyze_with_ai(subject: str, body: str) -> AnalysisResult:
    # Try Hugging Face first
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if hf_api_key:
        try:
            print("Using Hugging Face AI for analysis...")
            hf_analyzer = HuggingFaceAnalyzer(hf_api_key)
            result_data = hf_analyzer.analyze_email_with_ai(subject, body)
            return AnalysisResult(**result_data)
        except Exception as e:
            print(f"Hugging Face analysis failed: {e}")
            print("Falling back to local analyzer...")
    
    # Fallback to local analyzer
    print("Using local rule-based analyzer...")
    local_analyzer = LocalEmailAnalyzer()
    result_data = local_analyzer.analyze_email(subject, body)
    
    # Add note that this is from local analysis
    result_data["verdict"] += " (Local Analysis)"
    
    return AnalysisResult(**result_data)


# --- API Endpoints ---
@app.post("/qualify", response_model=AnalysisResult)
async def qualify_email(email_input: EmailInput, request: Request):
    start_time = time.time()
    client_ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
    user_agent = request.headers.get("user-agent", "Unknown")
    error_occurred = False
    error_message = None
    
    try:
        result = await analyze_with_ai(email_input.subject, email_input.email_body)
        
        # Log successful request
        if ADMIN_ENABLED and analytics_db:
            processing_time = int((time.time() - start_time) * 1000)  # Convert to ms
            ai_enhanced = "(AI Enhanced)" in result.verdict
            
            analytics_db.log_request(
                ip=client_ip,
                user_agent=user_agent,
                subject_len=len(email_input.subject),
                body_len=len(email_input.email_body),
                score=result.overallScore,
                ai_enhanced=ai_enhanced,
                processing_time=processing_time,
                error=False
            )
        
        return result
        
    except Exception as e:
        error_occurred = True
        error_message = str(e)
        
        # Log failed request
        if ADMIN_ENABLED and analytics_db:
            processing_time = int((time.time() - start_time) * 1000)
            
            analytics_db.log_request(
                ip=client_ip,
                user_agent=user_agent,
                subject_len=len(email_input.subject),
                body_len=len(email_input.email_body),
                score=0,
                ai_enhanced=False,
                processing_time=processing_time,
                error=True,
                error_msg=error_message
            )
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {error_message}")

@app.get("/")
async def read_root():
    return {"status": "InboxQualify API is running!", "admin_available": ADMIN_ENABLED}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "admin_enabled": ADMIN_ENABLED
    }