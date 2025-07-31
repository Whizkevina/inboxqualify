# main.py - ENHANCED VERSION WITH SUPABASE SUPPORT

# 1. Import necessary libraries
import os
import sys
import json
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_analyzer import LocalEmailAnalyzer
from huggingface_analyzer import HuggingFaceAnalyzer

# Load environment variables from .env file
load_dotenv()

# --- DATABASE CONFIGURATION ---
# Try to initialize Supabase first, fallback to SQLite
try:
    from supabase_db import get_db
    db = get_db()
    print("✅ Supabase PostgreSQL database connected successfully!")
    DB_TYPE = "supabase"
except Exception as e:
    print(f"⚠️ Supabase connection failed: {e}")
    print("🔄 Using SQLite fallback database")
    from admin_dashboard import AnalyticsDB
    db = AnalyticsDB()
    DB_TYPE = "sqlite"

# --- EMAIL ALERTS CONFIGURATION ---
try:
    from email_alerts import EmailAlertSystem
    email_alerts = EmailAlertSystem(db)
    print("✅ Email alert system initialized")
except Exception as e:
    print(f"⚠️ Email alerts initialization failed: {e}")
    email_alerts = None

# --- API KEY CONFIGURATION ---
try:
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_api_key:
        print("✅ Hugging Face API key loaded successfully!")
    else:
        print("⚠️ HUGGINGFACE_API_KEY not set. Will use local analyzer only.")
except Exception as e:
    print(f"❌ Error loading API keys: {e}")
    hf_api_key = None

# --- App Setup & CORS ---
app = FastAPI(
    title="InboxQualify API", 
    description="Email Qualification Service with Supabase PostgreSQL", 
    version="2.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Basic Auth for admin endpoints
security = HTTPBasic()

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    # Try database authentication first
    if DB_TYPE == "supabase" and hasattr(db, 'verify_admin_user'):
        try:
            user = db.verify_admin_user(credentials.username, credentials.password)
            if user:
                return user
        except Exception as e:
            print(f"DB auth failed: {e}")
    
    # Fallback to environment variables
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip("'\"")
    admin_password = os.getenv("ADMIN_PASSWORD", "password").strip("'\"")
    
    if credentials.username == admin_username and credentials.password == admin_password:
        return {"username": credentials.username, "role": "admin"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

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
async def analyze_with_ai(subject: str, body: str, request: Request) -> AnalysisResult:
    start_time = time.time()
    ip_address = request.client.host if request and request.client else "unknown"
    ai_model = None
    error_message = None
    
    # Try Hugging Face first
    if hf_api_key:
        try:
            print("🤖 Using Hugging Face AI for analysis...")
            ai_model = "huggingface"
            hf_analyzer = HuggingFaceAnalyzer(hf_api_key)
            result_data = hf_analyzer.analyze_email_with_ai(subject, body)
            
            response_time = time.time() - start_time
            
            # Log to database if Supabase is available
            if DB_TYPE == "supabase":
                try:
                    classification = {
                        "breakdown": [cat.dict() for cat in AnalysisResult(**result_data).breakdown],
                        "verdict": result_data["verdict"]
                    }
                    
                    db.log_email_analysis(
                        ip_address=ip_address,
                        email_content=f"Subject: {subject}\\n\\nBody: {body}",
                        sender_name="Unknown",
                        sender_email="unknown@unknown.com",
                        score=result_data["overallScore"],
                        response_time=response_time,
                        ai_model=ai_model,
                        error_message="",
                        classification=classification
                    )
                except Exception as log_error:
                    print(f"⚠️ Logging failed: {log_error}")
            
            return AnalysisResult(**result_data)
            
        except Exception as e:
            error_message = str(e)
            print(f"❌ Hugging Face analysis failed: {e}")
            print("🔄 Falling back to local analyzer...")
    
    # Fallback to local analyzer
    print("🏠 Using local rule-based analyzer...")
    ai_model = "local"
    local_analyzer = LocalEmailAnalyzer()
    result_data = local_analyzer.analyze_email(subject, body)
    result_data["verdict"] += " (Local Analysis)"
    
    response_time = time.time() - start_time
    
    # Log to database if Supabase is available
    if DB_TYPE == "supabase":
        try:
            classification = {
                "breakdown": result_data["breakdown"],
                "verdict": result_data["verdict"]
            }
            
            db.log_email_analysis(
                ip_address=ip_address,
                email_content=f"Subject: {subject}\\n\\nBody: {body}",
                sender_name="Unknown",
                sender_email="unknown@unknown.com",
                score=result_data["overallScore"],
                response_time=response_time,
                ai_model=ai_model,
                error_message=error_message or "",
                classification=classification
            )
        except Exception as log_error:
            print(f"⚠️ Logging failed: {log_error}")
    
    return AnalysisResult(**result_data)

# --- API Endpoints ---
@app.post("/qualify", response_model=AnalysisResult)
async def qualify_email(email_input: EmailInput, request: Request):
    """Analyze email and return qualification score"""
    return await analyze_with_ai(email_input.subject, email_input.email_body, request)

@app.get("/")
def read_root():
    """API health check"""
    return {
        "status": "InboxQualify API is running!", 
        "version": "2.0.0",
        "database": DB_TYPE,
        "features": {
            "supabase": DB_TYPE == "supabase",
            "email_alerts": email_alerts is not None,
            "huggingface_ai": hf_api_key is not None
        }
    }

# --- Admin Dashboard Endpoints ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(admin_user = Depends(get_current_admin)):
    """Serve admin dashboard"""
    try:
        # Use Phase 2 dashboard if available
        dashboard_path = "admin_templates/dashboard_phase2.html"
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as file:
                return HTMLResponse(content=file.read())
        else:
            # Fallback to basic dashboard
            dashboard_path = "admin_templates/dashboard.html"
            with open(dashboard_path, 'r', encoding='utf-8') as file:
                return HTMLResponse(content=file.read())
    except Exception as e:
        return HTMLResponse(f"<h1>Dashboard Error</h1><p>{str(e)}</p>", status_code=500)

@app.get("/admin/stats")
async def get_admin_stats(admin_user = Depends(get_current_admin)):
    """Get basic admin statistics"""
    try:
        if DB_TYPE == "supabase":
            stats = db.get_usage_stats()
        else:
            # SQLite fallback with basic stats
            stats = {
                "total_requests": 0,
                "today_requests": 0,
                "average_score": 0,
                "error_rate": 0,
                "unique_ips": 0,
                "last_24h_requests": 0
            }
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                db.log_admin_action(admin_user.get('username', 'admin'), 'view_stats')
        except:
            pass
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/admin/analytics/advanced")
async def get_advanced_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ip_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    admin_user = Depends(get_current_admin)
):
    """Get advanced analytics with filtering"""
    try:
        if DB_TYPE == "supabase":
            analytics = db.get_advanced_analytics(start_date, end_date, ip_filter, min_score, max_score)
        else:
            # SQLite fallback
            analytics = {
                "filtered_requests": 0,
                "score_stats": {"min_score": 0, "max_score": 0, "avg_score": 0, "total_requests": 0},
                "hourly_data": [],
                "unique_ips": 0,
                "error_count": 0
            }
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                db.log_admin_action(
                    admin_user.get('username', 'admin'), 
                    'advanced_analytics',
                    f"Filters: {start_date}-{end_date}, IP: {ip_filter}, Score: {min_score}-{max_score}"
                )
        except:
            pass
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/admin/users")
async def get_admin_users(admin_user = Depends(get_current_admin)):
    """Get all admin users"""
    try:
        if DB_TYPE == "supabase":
            users = db.get_admin_users()
        else:
            users = []
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                db.log_admin_action(admin_user.get('username', 'admin'), 'view_admin_users')
        except:
            pass
        
        return {"admin_users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Users error: {str(e)}")

@app.post("/admin/alerts/test")
async def test_email_alerts(admin_user = Depends(get_current_admin)):
    """Test email alert system"""
    try:
        if email_alerts:
            # For now, just return success - actual email testing requires proper setup
            message = "Email alert system is configured and ready"
        else:
            message = "Email alert system not initialized"
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                db.log_admin_action(admin_user.get('username', 'admin'), 'test_email_alerts')
        except:
            pass
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert test error: {str(e)}")

@app.get("/admin/audit-log")
async def get_audit_log(admin_user = Depends(get_current_admin)):
    """Get admin audit log"""
    try:
        if DB_TYPE == "supabase":
            audit_log = db.get_admin_audit_log()
        else:
            audit_log = []
        
        return {"audit_log": audit_log}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit log error: {str(e)}")

@app.get("/admin/health")
async def admin_health_check(admin_user = Depends(get_current_admin)):
    """Check system health"""
    try:
        if DB_TYPE == "supabase":
            health = db.health_check()
        else:
            health = {
                "status": "healthy",
                "connection": "active",
                "database": "sqlite_fallback",
                "features": {
                    "advanced_analytics": False,
                    "audit_logging": False,
                    "multi_admin": False
                }
            }
        
        # Add system information
        health["database_type"] = DB_TYPE
        health["email_alerts"] = email_alerts is not None
        health["ai_service"] = "huggingface" if hf_api_key else "local"
        
        return health
    except Exception as e:
        return {"status": "error", "error": str(e), "database_type": DB_TYPE}

# Serve static files
@app.get("/css/{file_path}")
async def serve_css(file_path: str):
    """Serve CSS files"""
    file_location = f"css/{file_path}"
    if os.path.exists(file_location):
        return FileResponse(file_location, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/js/{file_path}")
async def serve_js(file_path: str):
    """Serve JavaScript files"""
    file_location = f"js/{file_path}"
    if os.path.exists(file_location):
        return FileResponse(file_location, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JavaScript file not found")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting InboxQualify API v2.0.0 with {DB_TYPE} database...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
