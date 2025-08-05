# main.py - FINAL VERSION WITH SUPABASE

# 1. Import necessary libraries
import os
import sys
import json
import time
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_analyzer import LocalEmailAnalyzer
from huggingface_analyzer import HuggingFaceAnalyzer
from supabase_db import get_db  # Supabase database connection
from admin_dashboard import AnalyticsDB  # Keep for backward compatibility
from email_alerts import EmailAlertSystem

# Load environment variables from .env file
load_dotenv()

# --- API KEY CONFIGURATION ---
# Load API keys from environment variables
try:
    # Try Hugging Face first (our new primary AI)
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_api_key:
        print("Warning: HUGGINGFACE_API_KEY not set. Will use local analyzer only.")
    else:
        print("✅ Hugging Face API key loaded successfully!")
    
    # Initialize Supabase database
    try:
        db = get_db()
        print("✅ Supabase database connected successfully!")
    except Exception as e:
        print(f"⚠️ Supabase connection failed: {e}")
        print("📋 Please configure SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        # Fallback to SQLite for development
        db = AnalyticsDB()
        print("🔄 Using SQLite fallback database")
    
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    print("🔄 Will use local analyzer and SQLite as fallback.")
    db = AnalyticsDB()

# Initialize email alert system
try:
    email_alerts = EmailAlertSystem(db)
    print("✅ Email alert system initialized")
except Exception as e:
    print(f"⚠️ Email alerts initialization failed: {e}")
    email_alerts = None

# --- App Setup & CORS ---
origins = ["*"] # Allows all origins for local development
app = FastAPI(title="InboxQualify API", description="Email Qualification Service with Supabase", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Basic Auth for admin endpoints
security = HTTPBasic()

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    # Try database authentication first
    try:
        user = db.verify_admin_user(credentials.username, credentials.password)
        if user:
            return user
    except:
        pass
    
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
    classification = None
    
    # Try Hugging Face first
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if hf_api_key:
        try:
            print("🤖 Using Hugging Face AI for analysis...")
            ai_model = "huggingface"
            hf_analyzer = HuggingFaceAnalyzer(hf_api_key)
            result_data = hf_analyzer.analyze_email_with_ai(subject, body)
            
            # Extract additional classification data
            classification = {
                "breakdown": [cat.model_dump() for cat in AnalysisResult(**result_data).breakdown],
                "verdict": result_data["verdict"]
            }
            
            response_time = time.time() - start_time
            
            # Log to database (check if it's Supabase or SQLite)
            try:
                if hasattr(db, 'log_email_analysis'):
                    # Supabase database
                    db.log_email_analysis(
                        ip_address=ip_address,
                        email_content=f"Subject: {subject}\n\nBody: {body}",
                        sender_name="Unknown",
                        sender_email="unknown@unknown.com",
                        score=result_data["overallScore"],
                        response_time=response_time,
                        ai_model=ai_model,
                        error_message=error_message or "",
                        classification=classification
                    )
                else:
                    # SQLite fallback - no logging for now
                    print("📝 Using SQLite fallback - analytics logging disabled")
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
    
    # Add note that this is from local analysis
    result_data["verdict"] += " (Local Analysis)"
    
    response_time = time.time() - start_time
    
    # Extract classification data for local analysis
    classification = {
        "breakdown": [cat for cat in result_data["breakdown"]],
        "verdict": result_data["verdict"]
    }
    
    # Log to database
    try:
        if hasattr(db, 'log_email_analysis'):
            # Supabase database
            db.log_email_analysis(
                ip_address=ip_address,
                email_content=f"Subject: {subject}\n\nBody: {body}",
                sender_name="Unknown",
                sender_email="unknown@unknown.com",
                score=result_data["overallScore"],
                response_time=response_time,
                ai_model=ai_model,
                error_message=error_message or "",
                classification=classification
            )
        else:
            # SQLite fallback - no logging for now
            print("📝 Using SQLite fallback - analytics logging disabled")
    except Exception as log_error:
        print(f"⚠️ Logging failed: {log_error}")
    
    return AnalysisResult(**result_data)


# --- API Endpoint ---
@app.post("/qualify", response_model=AnalysisResult)
async def qualify_email(email_input: EmailInput, request: Request):
    """Analyze email and return qualification score"""
    return await analyze_with_ai(email_input.subject, email_input.email_body, request)

@app.get("/")
def read_root():
    """API health check"""
    return {
        "status": "InboxQualify API with Supabase is running!", 
        "version": "2.0.0",
        "database": "supabase" if hasattr(db, 'log_email_analysis') else "sqlite_fallback"
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
        if hasattr(db, 'get_usage_stats'):
            # Supabase database
            stats = db.get_usage_stats()
        else:
            # SQLite fallback
            stats = {
                "total_requests": 0,
                "today_requests": 0,
                "average_score": 0,
                "error_rate": 0,
                "unique_ips": 0,
                "last_24h_requests": 0
            }
        
        # Log admin action
        if hasattr(db, 'log_admin_action'):
            db.log_admin_action(admin_user.get('username', 'admin'), 'view_stats')
        
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
        if hasattr(db, 'get_advanced_analytics'):
            # Supabase database
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
        
        # Log admin action
        if hasattr(db, 'log_admin_action'):
            db.log_admin_action(
                admin_user.get('username', 'admin'), 
                'advanced_analytics',
                f"Filters: {start_date}-{end_date}, IP: {ip_filter}, Score: {min_score}-{max_score}"
            )
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/admin/users")
async def get_admin_users(admin_user = Depends(get_current_admin)):
    """Get all admin users"""
    try:
        if hasattr(db, 'get_admin_users'):
            # Supabase database
            users = db.get_admin_users()
        else:
            # SQLite fallback
            users = []
        
        # Log admin action
        if hasattr(db, 'log_admin_action'):
            db.log_admin_action(admin_user.get('username', 'admin'), 'view_admin_users')
        
        return {"admin_users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Users error: {str(e)}")

@app.post("/admin/alerts/test")
async def test_email_alerts(admin_user = Depends(get_current_admin)):
    """Test email alert system"""
    try:
        if email_alerts:
            # Run email alert checks
            email_alerts.check_and_send_alerts()
            message = "Email alert tests completed. Check logs for results."
        else:
            message = "Email alert system not initialized"
        
        # Log admin action
        if hasattr(db, 'log_admin_action'):
            db.log_admin_action(admin_user.get('username', 'admin'), 'test_email_alerts')
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert test error: {str(e)}")

@app.get("/admin/audit-log")
async def get_audit_log(admin_user = Depends(get_current_admin)):
    """Get admin audit log"""
    try:
        if hasattr(db, 'get_admin_audit_log'):
            # Supabase database
            audit_log = db.get_admin_audit_log()
        else:
            # SQLite fallback
            audit_log = []
        
        return {"audit_log": audit_log}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit log error: {str(e)}")

@app.get("/admin/health")
async def admin_health_check(admin_user = Depends(get_current_admin)):
    """Check system health"""
    try:
        if hasattr(db, 'health_check'):
            # Supabase database
            health = db.health_check()
        else:
            # SQLite fallback
            health = {
                "status": "healthy",
                "connection": "active",
                "database": "sqlite_fallback"
            }
        
        return health
    except Exception as e:
        return {"status": "error", "error": str(e)}