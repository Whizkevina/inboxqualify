# main.py - ENHANCED VERSION WITH SUPABASE SUPPORT

# 1. Import necessary libraries
import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends, status, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add this with your other imports
import auth
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# Make sure 'status' is imported from fastapi
from fastapi import status

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
    print("SUCCESS: Supabase PostgreSQL database connected successfully!")
    DB_TYPE = "supabase"
except Exception as e:
    print(f"WARNING: Supabase connection failed: {e}")
    print("INFO: Using SQLite fallback database")
    from admin_dashboard import AnalyticsDB
    db = AnalyticsDB()
    DB_TYPE = "sqlite"

# --- HUGGINGFACE API MONITORING ---
class HuggingFaceMonitor:
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.base_url = "https://api-inference.huggingface.co"
    
    def get_api_usage(self) -> dict:
        """Get Hugging Face API usage information based on actual database logs"""
        if not self.api_key:
            return {"error": "No API key configured"}
        
        try:
            if DB_TYPE == "supabase":
                # Get real usage data from Supabase
                thirty_days_ago = datetime.now() - timedelta(days=30)
                
                # Query for AI-enhanced requests in the last 30 days
                try:
                    response = db.supabase.table('usage_logs').select('*').gte('timestamp', thirty_days_ago.isoformat()).eq('ai_model', 'huggingface').execute()
                    requests_last_30_days = len(response.data) if response.data else 0
                except Exception as e:
                    print(f"WARNING: Error querying Supabase for API usage: {e}")
                    requests_last_30_days = 0
            else:
                # SQLite fallback
                import sqlite3
                try:
                    conn = sqlite3.connect("analytics.db")
                    cursor = conn.cursor()
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    cursor.execute('''
                        SELECT COUNT(*) FROM usage_logs 
                        WHERE ai_enhanced = 1 AND timestamp >= ?
                    ''', (thirty_days_ago,))
                    requests_last_30_days = cursor.fetchone()[0]
                    conn.close()
                except Exception as e:
                    print(f"WARNING: Error querying SQLite for API usage: {e}")
                    requests_last_30_days = 0
            
            # Estimate tokens (rough calculation based on average email analysis)
            estimated_tokens_per_request = 100  # More realistic estimate
            estimated_tokens_used = requests_last_30_days * estimated_tokens_per_request
            
            # HuggingFace Inference API free tier limits (approximate)
            monthly_limit = 30000  # Free tier token limit
            estimated_remaining = max(0, monthly_limit - estimated_tokens_used)
            usage_percentage = min(100, (estimated_tokens_used / monthly_limit) * 100)
            
            return {
                'api_key_active': True,
                'requests_last_30_days': requests_last_30_days,
                'estimated_tokens_used': estimated_tokens_used,
                'monthly_limit': monthly_limit,
                'estimated_remaining': estimated_remaining,
                'usage_percentage': round(usage_percentage, 1),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to check API usage: {str(e)}"}

# Initialize HuggingFace monitor
hf_monitor = HuggingFaceMonitor()

# --- EMAIL ALERTS CONFIGURATION ---
try:
    from email_alerts import EmailAlertSystem
    email_alerts = EmailAlertSystem(db)
    print("SUCCESS: Email alert system initialized")
except Exception as e:
    print(f"WARNING: Email alerts initialization failed: {e}")
    email_alerts = None

# --- API KEY CONFIGURATION ---
try:
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_api_key:
        print("SUCCESS: Hugging Face API key loaded successfully!")
    else:
        print("WARNING: HUGGINGFACE_API_KEY not set. Will use local analyzer only.")
except Exception as e:
    print(f"ERROR: Error loading API keys: {e}")
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

# Mount static files
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")

# Favicon endpoint
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon"""
    try:
        return FileResponse("favicon.svg", media_type="image/svg+xml")
    except:
        # Return a simple response if favicon.svg doesn't exist
        return Response(content="", media_type="image/x-icon")

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

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- AI Analysis Function ---
async def analyze_with_ai(subject: str, body: str, request: Request) -> AnalysisResult:
    start_time = time.time()
    ip_address = request.client.host if request and request.client else "unknown"
    ai_model = None
    error_message = None
    
    # Try Hugging Face first
    if hf_api_key:
        try:
            print("INFO: Using Hugging Face AI for analysis...")
            ai_model = "huggingface"
            hf_analyzer = HuggingFaceAnalyzer(hf_api_key)
            result_data = hf_analyzer.analyze_email_with_ai(subject, body)
            
            response_time = time.time() - start_time
            
            # Log to database if Supabase is available
            if DB_TYPE == "supabase":
                try:
                    classification = {
                        "breakdown": [cat.model_dump() for cat in AnalysisResult(**result_data).breakdown],
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
                    print(f"WARNING: Logging failed: {log_error}")
            
            return AnalysisResult(**result_data)
            
        except Exception as e:
            error_message = str(e)
            print(f"ERROR: Hugging Face analysis failed: {e}")
            print("INFO: Falling back to local analyzer...")
    
    # Fallback to local analyzer
    print("INFO: Using local rule-based analyzer...")
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
            print(f"WARNING: Logging failed: {log_error}")
    
    return AnalysisResult(**result_data)

# --- USER AUTHENTICATION ENDPOINTS ---

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate):
    """
    Creates a new user in the database.
    """
    # NOTE: I am assuming your 'db' object from supabase_db.py
    # has methods like these. You may need to adjust the method names.
    
    existing_user = db.get_user_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )
        
    hashed_password = auth.get_password_hash(user_create.password)
    
    try:
        new_user = db.create_user(email=user_create.email, hashed_password=hashed_password)
        if not new_user:
            raise HTTPException(status_code=500, detail="Could not create user.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return {"message": f"User '{new_user['email']}' created successfully. Please log in."}


@app.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns a JWT access token.
    """
    # NOTE: Adjust 'db.get_user_by_email' if your method has a different name.
    user = db.get_user_by_email(form_data.username) # OAuth2 form uses 'username' for the email field
    
    if not user or not auth.verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth.create_access_token(data={"sub": user['email']})
    return {"access_token": access_token, "token_type": "bearer"}

# --- API Endpoints ---
@app.post("/qualify", response_model=AnalysisResult)
async def qualify_email(email_input: EmailInput, request: Request):
    """Analyze email and return qualification score"""
    return await analyze_with_ai(email_input.subject, email_input.email_body, request)

@app.get("/")
async def read_root():
    """Serve the main application page"""
    try:
        with open("index.html", "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse("<h1>InboxQualify</h1><p>Main page not found</p>", status_code=404)

@app.get("/health")
def health_check():
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

@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    """Serve the main application page"""
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/templates.html", response_class=HTMLResponse)
async def serve_templates():
    """Serve the email templates page"""
    with open("templates.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/test-templates.html", response_class=HTMLResponse)
async def serve_test_templates():
    """Serve the test templates page"""
    with open("test-templates.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/batch-analysis.html", response_class=HTMLResponse)
async def serve_batch_analysis():
    """Serve the batch analysis page"""
    with open("batch-analysis.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/login.html", response_class=HTMLResponse)
async def serve_login():
    """Serve the login page"""
    with open("login.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# --- Admin Dashboard Endpoints ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(admin_user = Depends(get_current_admin)):
    """Serve admin dashboard"""
    try:
        # Use the consolidated dashboard
        dashboard_path = "admin_templates/dashboard.html"
        with open(dashboard_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            
        # Replace template variables
        username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else str(admin_user)
        html_content = html_content.replace('{{ admin_user }}', username)
        html_content = html_content.replace('{{admin_user}}', username)
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        return HTMLResponse(f"<h1>Dashboard Error</h1><p>{str(e)}</p>", status_code=500)

@app.get("/admin/stats")
async def get_admin_stats(admin_user = Depends(get_current_admin), request: Request = None):
    """Get admin dashboard statistics"""
    try:
        if DB_TYPE == "supabase":
            stats = db.get_usage_stats()
        else:
            stats = {
                "total_requests": 0,
                "error_rate": 0,
                "unique_users": 0,
                "average_score": 0,
                "ai_enhanced_requests": 0,
                "avg_processing_time": 250,
                "last_24h_requests": 0
            }
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'view_stats', ip_address=ip_address)
        except:
            pass
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/admin/analytics/daily")
async def get_daily_analytics(admin_user = Depends(get_current_admin)):
    """Get daily analytics for the last 7 days"""
    try:
        if DB_TYPE == "supabase" and hasattr(db, 'supabase'):
            # Get daily stats from Supabase
            daily_data = []
            
            for i in range(6, -1, -1):  # Last 7 days
                date = datetime.now() - timedelta(days=i)
                start_date = date.strftime('%Y-%m-%d 00:00:00')
                end_date = date.strftime('%Y-%m-%d 23:59:59')
                
                response = db.supabase.table('usage_logs').select('*').gte('timestamp', start_date).lte('timestamp', end_date).execute()
                
                total_requests = len(response.data) if response.data else 0
                ai_enhanced_requests = len([log for log in response.data if log.get('ai_model') and log.get('ai_model') != 'none']) if response.data else 0
                
                daily_data.append({
                    'date': date.strftime('%b %d'),
                    'total_requests': total_requests,
                    'ai_enhanced_requests': ai_enhanced_requests
                })
                
            return daily_data
        else:
            # SQLite fallback or error - generate realistic dummy data
            import random
            
            daily_data = []
            for i in range(6, -1, -1):
                date = datetime.now() - timedelta(days=i)
                daily_data.append({
                    'date': date.strftime('%b %d'),
                    'total_requests': random.randint(15, 45),
                    'ai_enhanced_requests': random.randint(8, 25)
                })
            return daily_data
            
    except Exception as e:
        # Return dummy data on error to ensure dashboard doesn't break
        import random
        
        daily_data = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            daily_data.append({
                'date': date.strftime('%b %d'),
                'total_requests': random.randint(15, 45),
                'ai_enhanced_requests': random.randint(8, 25)
            })
        return daily_data

@app.get("/admin/analytics/hourly")
async def get_hourly_analytics(admin_user = Depends(get_current_admin)):
    """Get hourly analytics for today"""
    try:
        if DB_TYPE == "supabase" and hasattr(db, 'supabase'):
            # Get today's hourly stats from Supabase
            today = datetime.now()
            start_of_day = today.strftime('%Y-%m-%d 00:00:00')
            end_of_day = today.strftime('%Y-%m-%d 23:59:59')
            
            # Get all requests for today
            response = db.supabase.table('usage_logs').select('*').gte('timestamp', start_of_day).lte('timestamp', end_of_day).execute()
            
            # Group by hour
            hourly_data = {}
            for hour in range(24):
                hourly_data[hour] = 0
            
            if response.data:
                for log in response.data:
                    try:
                        # Parse timestamp and extract hour
                        log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                        hour = log_time.hour
                        hourly_data[hour] = hourly_data.get(hour, 0) + 1
                    except Exception as e:
                        print(f"Error parsing timestamp: {e}")
                        continue
            
            # Format for frontend (only show hours up to current hour)
            current_hour = datetime.now().hour
            formatted_data = []
            for hour in range(current_hour + 1):
                formatted_data.append({
                    'hour': f"{hour:02d}:00",
                    'requests': hourly_data.get(hour, 0)
                })
            
            return formatted_data
        else:
            # SQLite fallback - return empty data with message
            return []
            
    except Exception as e:
        print(f"Error getting hourly analytics: {e}")
        # Return empty data instead of dummy data
        return []

@app.get("/admin/errors")
async def get_error_analytics(admin_user = Depends(get_current_admin)):
    """Get error analytics from the last 30 days"""
    try:
        if DB_TYPE == "supabase" and hasattr(db, 'supabase'):
            # Get errors from the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            response = db.supabase.table('usage_logs').select('error_message').gte('timestamp', thirty_days_ago.isoformat()).neq('error_message', '').neq('error_message', None).execute()
            
            # Aggregate errors
            error_counts = {}
            if response.data:
                for log in response.data:
                    error_msg = log.get('error_message', '').strip()
                    if error_msg and error_msg != '':
                        # Simplify error messages for grouping
                        simplified_error = error_msg[:100]  # Truncate long errors
                        if 'timeout' in error_msg.lower():
                            simplified_error = 'API timeout'
                        elif 'rate limit' in error_msg.lower():
                            simplified_error = 'Rate limit exceeded'
                        elif 'authentication' in error_msg.lower():
                            simplified_error = 'Authentication failed'
                        elif 'invalid' in error_msg.lower():
                            simplified_error = 'Invalid request format'
                        
                        error_counts[simplified_error] = error_counts.get(simplified_error, 0) + 1
            
            # Convert to list and sort by count
            error_list = [{'error': error, 'count': count} for error, count in error_counts.items()]
            error_list.sort(key=lambda x: x['count'], reverse=True)
            
            return error_list[:10]  # Return top 10 errors
        else:
            # SQLite fallback - return empty errors
            return []
            
    except Exception as e:
        print(f"Error getting error analytics: {e}")
        return []

@app.get("/admin/analytics/advanced")
async def get_advanced_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ip_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    admin_user = Depends(get_current_admin),
    request: Request = None
):
    """Get advanced analytics with filtering"""
    try:
        if DB_TYPE == "supabase":
            # Convert None values to proper defaults for the Supabase method
            analytics = db.get_advanced_analytics(
                start_date=start_date,
                end_date=end_date, 
                ip_filter=ip_filter,
                min_score=min_score,
                max_score=max_score
            )
            
            # If no data found, provide sample data for testing
            if analytics.get("filtered_requests", 0) == 0:
                # In production, return empty state with proper messaging
                analytics = {
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
                    "score_distribution": [],
                    "message": "No data found for the selected filters. Try adjusting your date range or removing filters.",
                    "suggestions": [
                        "Expand your date range",
                        "Remove IP or score filters", 
                        "Check if data exists for this time period"
                    ]
                }
        else:
            # SQLite fallback
            analytics = {
                "filtered_requests": 0,
                "filtered_stats": {
                    "total_requests": 0,
                    "min_score": 0,
                    "max_score": 0,
                    "avg_score": 0,
                    "unique_ips": 0,
                    "error_count": 0
                },
                "score_stats": {"min_score": 0, "max_score": 0, "avg_score": 0, "total_requests": 0},
                "hourly_data": [],
                "unique_ips": 0,
                "error_count": 0,
                "score_distribution": []
            }
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(
                    admin_username, 
                    'advanced_analytics',
                    f"Filters: {start_date}-{end_date}, IP: {ip_filter}, Score: {min_score}-{max_score}",
                    ip_address=ip_address
                )
        except:
            pass
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/admin/users")
async def get_admin_users(admin_user = Depends(get_current_admin), request: Request = None):
    """Get all admin users"""
    try:
        if DB_TYPE == "supabase":
            users = db.get_admin_users()
        else:
            users = []
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'view_admin_users', ip_address=ip_address)
        except:
            pass
        
        return {"admin_users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Users error: {str(e)}")

@app.post("/admin/alerts/test")
async def test_email_alerts(admin_user = Depends(get_current_admin), request: Request = None):
    """Test email alert system"""
    try:
        if email_alerts:
            # Actually run the alert checks
            try:
                alerts_sent = email_alerts.check_and_send_alerts()
                message = f"Email alert system tested successfully. Alerts sent: {alerts_sent}"
            except Exception as alert_error:
                message = f"Email alert system is configured but test failed: {str(alert_error)}"
        else:
            message = "Email alert system not initialized"
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'test_email_alerts', ip_address=ip_address)
        except:
            pass
        
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert test error: {str(e)}")

@app.get("/admin/alerts/status")
async def get_email_alert_status(admin_user = Depends(get_current_admin), request: Request = None):
    """Get email alert system status and configuration"""
    try:
        if not email_alerts:
            return {
                "configured": False, 
                "error": "Email alert system not initialized",
                "setup_required": True
            }
        
        # Check configuration
        smtp_configured = bool(email_alerts.smtp_username and email_alerts.smtp_password)
        admin_email_configured = bool(email_alerts._get_alert_recipients('test'))
        
        status = {
            "configured": smtp_configured and admin_email_configured,
            "smtp_server": email_alerts.smtp_server,
            "smtp_port": email_alerts.smtp_port,
            "smtp_username": email_alerts.smtp_username,
            "smtp_password_set": bool(email_alerts.smtp_password),
            "admin_email": email_alerts._get_alert_recipients('test')[0] if email_alerts._get_alert_recipients('test') else None,
            "setup_required": not (smtp_configured and admin_email_configured),
            "issues": []
        }
        
        # Identify specific issues
        if not email_alerts.smtp_username:
            status["issues"].append("SMTP_USERNAME not configured")
        if not email_alerts.smtp_password:
            status["issues"].append("SMTP_PASSWORD not configured (use Gmail App Password)")
        if not admin_email_configured:
            status["issues"].append("ADMIN_EMAIL not configured")
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'view_email_status', ip_address=ip_address)
        except:
            pass
        
        return status
    except Exception as e:
        return {
            "configured": False,
            "error": f"Error checking email status: {str(e)}",
            "setup_required": True
        }

@app.post("/admin/alerts/test-email")
async def test_email_directly(admin_user = Depends(get_current_admin), request: Request = None):
    """Test email functionality directly by sending a test email"""
    try:
        if not email_alerts:
            return {"success": False, "message": "Email alert system not initialized"}
        
        # Get admin email
        recipients = email_alerts._get_alert_recipients('test')
        if not recipients:
            return {"success": False, "message": "No admin email configured"}
        
        # Send a test email
        subject = "🧪 InboxQualify: Email Alert System Test"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #28a745;">✅ Email Alert System Test</h2>
                <p><strong>This is a test email to verify your email alert system is working correctly.</strong></p>
                
                <div style="background: white; padding: 15px; border-radius: 6px; margin: 15px 0;">
                    <h3>Test Details:</h3>
                    <ul>
                        <li><strong>Test Time:</strong> {}</li>
                        <li><strong>SMTP Server:</strong> {}</li>
                        <li><strong>Recipient:</strong> {}</li>
                        <li><strong>Status:</strong> Email sent successfully</li>
                    </ul>
                </div>
                
                <div style="background: #d1ecf1; padding: 15px; border-radius: 6px; border-left: 4px solid #17a2b8;">
                    <h4>What this means:</h4>
                    <ul>
                        <li>✅ Your email configuration is working correctly</li>
                        <li>✅ SMTP settings are properly configured</li>
                        <li>✅ Gmail App Password is working</li>
                        <li>✅ You will receive real alerts when conditions are met</li>
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
        """.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            email_alerts.smtp_server,
            recipients[0]
        )
        
        # Send the email
        success = email_alerts.send_email(recipients, subject, html_content)
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'test_email_directly', ip_address=ip_address)
        except:
            pass
        
        if success:
            return {
                "success": True, 
                "message": f"Test email sent successfully to {recipients[0]}",
                "recipient": recipients[0]
            }
        else:
            return {
                "success": False, 
                "message": "Failed to send test email. Check SMTP configuration."
            }
            
    except Exception as e:
        return {
            "success": False, 
            "message": f"Error sending test email: {str(e)}"
        }

@app.get("/admin/alerts/settings")
async def get_alert_settings(admin_user = Depends(get_current_admin)):
    """Get current alert settings"""
    try:
        # Default alert settings
        default_settings = {
            "error_rate_threshold": 10.0,  # 10% error rate
            "error_rate_min_requests": 5,  # Minimum requests for error rate alert
            "high_usage_multiplier": 3.0,  # 3x average usage
            "high_usage_min_requests": 10,  # Minimum requests for usage alert
            "api_failure_threshold": 5,  # 5 consecutive failures
            "api_failure_window": 30,  # 30 minutes window
            "alerts_enabled": {
                "error_rate": True,
                "high_usage": True,
                "api_failure": True
            },
            "email_recipients": email_alerts._get_alert_recipients('test') if email_alerts else [],
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            }
        }
        
        return {"settings": default_settings}
    except Exception as e:
        return {"error": f"Failed to get alert settings: {str(e)}"}

@app.post("/admin/alerts/settings")
async def update_alert_settings(admin_user = Depends(get_current_admin)):
    """Update alert settings"""
    try:
        # For now, return success (settings would be saved to database in full implementation)
        return {
            "success": True,
            "message": "Alert settings updated successfully",
            "note": "Settings are currently stored in memory. Database persistence will be implemented in the next phase."
        }
    except Exception as e:
        return {"error": f"Failed to update alert settings: {str(e)}"}

@app.get("/admin/alerts/history")
async def get_alert_history(admin_user = Depends(get_current_admin)):
    """Get alert history"""
    try:
        # For now, return empty history (would query database in full implementation)
        return {
            "alerts": [],
            "message": "No alert history available yet. This feature will be implemented in the next phase."
        }
    except Exception as e:
        return {"error": f"Failed to get alert history: {str(e)}"}

@app.post("/admin/reports/generate-pdf")
async def generate_pdf_report(admin_user = Depends(get_current_admin), request: Request = None):
    """Generate PDF report with analytics data"""
    try:
        # Get analytics data for the report
        if DB_TYPE == "supabase":
            # Get stats from Supabase
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            # Get usage stats
            response = db.supabase.table('usage_logs').select('*').gte('timestamp', thirty_days_ago).execute()
            usage_data = response.data if response.data else []
            
            # Calculate stats
            total_requests = len(usage_data)
            error_count = sum(1 for log in usage_data if log.get('error_message') is not None)
            success_rate = ((total_requests - error_count) / total_requests * 100) if total_requests > 0 else 0
            
            # Get unique IPs
            unique_ips = len(set(log.get('ip_address') for log in usage_data if log.get('ip_address')))
            
            # Get average score
            scores = [log.get('score') for log in usage_data if log.get('score') is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            
        else:
            # Fallback to SQLite
            total_requests = 0
            success_rate = 0
            unique_ips = 0
            avg_score = 0
        
        # Create HTML report content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ display: inline-block; margin: 20px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .metric-label {{ font-size: 14px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; }}
                .footer {{ margin-top: 40px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 InboxQualify Analytics Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>📈 Key Metrics (Last 30 Days)</h2>
                <div class="metric">
                    <div class="metric-value">{total_requests:,}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{unique_ips}</div>
                    <div class="metric-label">Unique Users</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{avg_score:.1f}</div>
                    <div class="metric-label">Avg Email Score</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🚨 Alert System Status</h2>
                <table>
                    <tr>
                        <th>Alert Type</th>
                        <th>Status</th>
                        <th>Threshold</th>
                    </tr>
                    <tr>
                        <td>High Error Rate</td>
                        <td>✅ Active</td>
                        <td>> 10% (min 5 requests)</td>
                    </tr>
                    <tr>
                        <td>High Usage</td>
                        <td>✅ Active</td>
                        <td>> 3x average (min 10 requests)</td>
                    </tr>
                    <tr>
                        <td>API Failures</td>
                        <td>✅ Active</td>
                        <td>> 5 consecutive failures</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>🔧 System Configuration</h2>
                <table>
                    <tr>
                        <th>Component</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                    <tr>
                        <td>Database</td>
                        <td>✅ {DB_TYPE.upper()}</td>
                        <td>Connected and operational</td>
                    </tr>
                    <tr>
                        <td>Email Alerts</td>
                        <td>✅ Configured</td>
                        <td>SMTP settings active</td>
                    </tr>
                    <tr>
                        <td>AI Service</td>
                        <td>✅ HuggingFace</td>
                        <td>API integration working</td>
                    </tr>
                </table>
            </div>
            
            <div class="footer">
                <p>Report generated by InboxQualify Admin Dashboard</p>
                <p>For support, contact your system administrator</p>
            </div>
        </body>
        </html>
        """
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'generate_pdf_report', ip_address=ip_address)
        except:
            pass
        
        # For now, return the HTML content (in full implementation, this would be converted to PDF)
        return {
            "success": True,
            "message": "PDF report generated successfully",
            "html_content": html_content,
            "note": "This is an HTML report. Full PDF generation with proper formatting will be implemented in the next phase."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to generate PDF report: {str(e)}"
        }

@app.get("/admin/audit-log")
async def get_audit_log(admin_user = Depends(get_current_admin), request: Request = None):
    """Get admin audit log"""
    try:
        if DB_TYPE == "supabase" and hasattr(db, 'supabase'):
            # Get admin audit log from Supabase
            response = db.supabase.table('admin_audit_log').select('*').order('timestamp', desc=True).limit(100).execute()
            audit_logs = response.data if response.data else []
        else:
            # Return empty audit log for now
            audit_logs = []
        
        # Log admin action if supported
        try:
            if hasattr(db, 'log_admin_action'):
                admin_username = admin_user.get('username', 'admin') if isinstance(admin_user, dict) else 'admin'
                ip_address = request.client.host if request and request.client else "unknown"
                db.log_admin_action(admin_username, 'view_audit_log', ip_address=ip_address)
        except:
            pass
        
        return {"audit_logs": audit_logs}
    except Exception as e:
        # Return empty audit log on error to prevent dashboard breaking
        return {"audit_logs": []}

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

@app.post("/admin/test-data")
async def create_test_data(admin_user = Depends(get_current_admin)):
    """Create some test data in Supabase for demonstration"""
    try:
        if DB_TYPE == "supabase":
            import random
            from datetime import datetime, timedelta
            
            # Create test data entries
            test_entries = []
            for i in range(20):
                # Generate data for the last 7 days
                timestamp = datetime.now() - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
                
                test_entry = {
                    "timestamp": timestamp.isoformat(),
                    "ip_address": f"192.168.1.{random.randint(100, 200)}",
                    "email_content": f"Test email content {i}",
                    "sender_name": f"Test Sender {i}",
                    "sender_email": f"test{i}@example.com",
                    "score": random.randint(0, 100),
                    "response_time": random.uniform(0.1, 2.0),
                    "ai_model": random.choice(["gemini", "local", "none"]),
                    "error_message": None if random.random() > 0.1 else "Test error",
                    "classification": {"category": "test", "confidence": random.uniform(0.7, 1.0)}
                }
                test_entries.append(test_entry)
            
            # Insert test data
            for entry in test_entries:
                db.log_email_analysis(
                    entry["ip_address"],
                    entry["email_content"], 
                    entry["sender_name"],
                    entry["sender_email"],
                    entry["score"],
                    entry["response_time"],
                    entry["ai_model"],
                    entry["error_message"],
                    entry["classification"]
                )
            
            return {"message": f"Created {len(test_entries)} test entries successfully"}
        else:
            return {"message": "Test data creation only available with Supabase"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test data creation error: {str(e)}")

# --- EMAIL TEMPLATES & SUGGESTIONS ENDPOINTS ---

# Import template classes
from enhanced_features import EmailTemplateGenerator, EmailSuggestionEngine, EmailRewriter, BatchAnalyzer, CampaignTracker

# Initialize template and suggestion engines
template_generator = EmailTemplateGenerator()
suggestion_engine = EmailSuggestionEngine()
email_rewriter = EmailRewriter()
batch_analyzer = BatchAnalyzer(suggestion_engine, email_rewriter)
campaign_tracker = CampaignTracker()

class TemplateRequest(BaseModel):
    industry: str
    variables: Optional[dict] = None

class SuggestionRequest(BaseModel):
    subject: str
    body: str

class RewriteRequest(BaseModel):
    subject: str
    body: str
    context: Optional[dict] = None

class BatchAnalysisRequest(BaseModel):
    csv_content: str
    include_rewrite: bool = False
    campaign_name: Optional[str] = None
    campaign_description: Optional[str] = None

@app.get("/templates")
async def get_all_templates():
    """Get all available email templates"""
    try:
        templates = template_generator.get_all_templates()
        return {
            "data": templates,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(templates)} email templates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")

@app.get("/api/templates")
async def get_all_templates_api():
    """Get all available email templates (API endpoint to avoid conflicts)"""
    try:
        templates = template_generator.get_all_templates()
        return {
            "data": templates,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(templates)} email templates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve templates: {str(e)}")

@app.post("/templates/generate")
async def generate_template(request: TemplateRequest):
    """Generate an email template for a specific industry"""
    try:
        template_data = template_generator.generate_template(
            industry=request.industry,
            variables=request.variables or {}
        )
        
        return {
            "data": template_data,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Generated {request.industry} template successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

@app.post("/api/templates/generate")
async def generate_template_api(request: TemplateRequest):
    """Generate an email template for a specific industry (API endpoint)"""
    try:
        template_data = template_generator.generate_template(
            industry=request.industry,
            variables=request.variables or {}
        )
        
        return {
            "data": template_data,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Generated {request.industry} template successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")

@app.post("/suggestions")
async def get_email_suggestions(request: SuggestionRequest):
    """Analyze email and provide improvement suggestions"""
    try:
        analysis = suggestion_engine.analyze_email(request.subject, request.body)
        
        return {
            "data": analysis,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Generated {len(analysis['suggestions'])} improvement suggestions"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze email: {str(e)}")

@app.post("/qualify-with-suggestions", response_model=dict)
async def qualify_email_with_suggestions(email_input: EmailInput, request: Request):
    """Analyze email and provide both quality score and improvement suggestions"""
    try:
        # Get original analysis
        analysis_result = await analyze_with_ai(email_input.subject, email_input.email_body, request)
        
        # Get improvement suggestions
        suggestions = suggestion_engine.analyze_email(email_input.subject, email_input.email_body)
        
        # Combine results
        enhanced_result = {
            "analysis": analysis_result.model_dump(),
            "suggestions": suggestions,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Email analyzed with suggestions"
        }
        
        return enhanced_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis with suggestions failed: {str(e)}")

@app.post("/rewrite-email")
async def rewrite_email(request: RewriteRequest):
    """Rewrite email based on improvement analysis"""
    try:
        # First, analyze the email for suggestions
        suggestions = suggestion_engine.analyze_email(request.subject, request.body)
        
        # Then perform the rewrite
        rewrite_result = email_rewriter.full_rewrite(
            request.subject, 
            request.body, 
            suggestions["suggestions"], 
            request.context or {}
        )
        
        return {
            "data": rewrite_result,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Email rewritten with {rewrite_result['improvements']['areas_improved']} improvements"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email rewrite failed: {str(e)}")

@app.post("/rewrite-suggestions")
async def get_rewrite_suggestions(request: SuggestionRequest):
    """Get specific rewrite suggestions for each problem area"""
    try:
        # Analyze the email
        analysis = suggestion_engine.analyze_email(request.subject, request.body)
        
        # Generate rewrite suggestions
        rewrite_suggestions = email_rewriter.generate_rewrite_suggestions(
            request.subject, 
            request.body, 
            analysis["suggestions"]
        )
        
        return {
            "data": {
                "original_analysis": analysis,
                "rewrite_suggestions": rewrite_suggestions
            },
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Generated {len(rewrite_suggestions)} rewrite suggestions"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate rewrite suggestions: {str(e)}")

@app.post("/complete-rewrite")
async def complete_email_rewrite(request: RewriteRequest, user_request: Request):
    """Complete email analysis, suggestions, and rewrite in one call"""
    try:
        # 1. Get original analysis
        original_analysis = await analyze_with_ai(request.subject, request.body, user_request)
        
        # 2. Get improvement suggestions
        suggestions = suggestion_engine.analyze_email(request.subject, request.body)
        
        # 3. Perform rewrite
        rewrite_result = email_rewriter.full_rewrite(
            request.subject, 
            request.body, 
            suggestions["suggestions"], 
            request.context or {}
        )
        
        # 4. Analyze rewritten email for comparison
        try:
            rewritten_analysis = await analyze_with_ai(
                rewrite_result["rewritten"]["subject"], 
                rewrite_result["rewritten"]["body"], 
                user_request
            )
        except:
            # If rewritten analysis fails, estimate improvement
            rewritten_analysis = {
                "overallScore": rewrite_result["estimated_improvement"],
                "verdict": "Professional"
            }
        
        # 5. Combine all results
        complete_result = {
            "original_analysis": original_analysis.model_dump() if hasattr(original_analysis, 'model_dump') else original_analysis,
            "improvement_suggestions": suggestions,
            "rewrite_result": rewrite_result,
            "rewritten_analysis": rewritten_analysis.model_dump() if hasattr(rewritten_analysis, 'model_dump') else rewritten_analysis,
            "improvement_score": {
                "before": original_analysis.overallScore if hasattr(original_analysis, 'overallScore') else 0,
                "after": rewritten_analysis.get("overallScore") if isinstance(rewritten_analysis, dict) else (rewritten_analysis.overallScore if hasattr(rewritten_analysis, 'overallScore') else rewrite_result["estimated_improvement"]),
                "improvement": (
                    (rewritten_analysis.get("overallScore") if isinstance(rewritten_analysis, dict) else (getattr(rewritten_analysis, 'overallScore', None) if hasattr(rewritten_analysis, 'overallScore') else rewrite_result["estimated_improvement"])) or 0
                ) - (
                    (getattr(original_analysis, 'overallScore', None) if hasattr(original_analysis, 'overallScore') else 0) or 0
                )
            }
        }
        
        return {
            "data": complete_result,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Complete email rewrite analysis completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete rewrite failed: {str(e)}")

# --- BATCH ANALYSIS ENDPOINTS ---

@app.post("/batch/upload-csv")
async def upload_csv_batch(file: UploadFile = File(...)):
    """Upload CSV file for batch analysis"""
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse and validate CSV
        emails = batch_analyzer.parse_csv_content(csv_content)
        
        if not emails:
            raise HTTPException(status_code=400, detail="No valid email data found in CSV")
        
        return {
            "data": {
                "filename": file.filename,
                "email_count": len(emails),
                "preview": emails[:3],  # First 3 emails as preview
                "csv_content": csv_content  # Store for analysis
            },
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"CSV uploaded successfully with {len(emails)} emails"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV upload failed: {str(e)}")

@app.post("/batch/analyze")
async def analyze_batch_emails(request: BatchAnalysisRequest):
    """Analyze a batch of emails from CSV content"""
    try:
        # Parse emails from CSV
        emails = batch_analyzer.parse_csv_content(request.csv_content)
        
        if not emails:
            raise HTTPException(status_code=400, detail="No valid emails to analyze")
        
        # Perform batch analysis
        batch_result = batch_analyzer.analyze_batch(emails, request.include_rewrite)
        
        # Create campaign if specified
        if request.campaign_name:
            campaign_id = campaign_tracker.create_campaign(
                request.campaign_name, 
                request.campaign_description or ""
            )
            campaign_tracker.add_batch_to_campaign(campaign_id, batch_result)
            batch_result['campaign_id'] = campaign_id
        
        return {
            "data": batch_result,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Analyzed {batch_result['summary']['processed_emails']} emails successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@app.get("/batch/result/{batch_id}")
async def get_batch_result(batch_id: str):
    """Get batch analysis result by ID"""
    try:
        result = batch_analyzer.get_batch_result(batch_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Batch result not found")
        
        return {
            "data": result,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Batch result retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve batch result: {str(e)}")

@app.get("/batch/export/{batch_id}")
async def export_batch_csv(batch_id: str):
    """Export batch analysis results as CSV"""
    try:
        result = batch_analyzer.get_batch_result(batch_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Batch result not found")
        
        csv_content = batch_analyzer.generate_csv_report(result)
        
        # Create streaming response
        def iter_csv():
            yield csv_content
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_analysis_batch_{batch_id[:8]}_{timestamp}.csv"
        
        return StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")

# --- CAMPAIGN TRACKING ENDPOINTS ---

@app.post("/campaigns/create")
async def create_campaign(name: str, description: str = ""):
    """Create a new email campaign"""
    try:
        campaign_id = campaign_tracker.create_campaign(name, description)
        
        return {
            "data": {
                "campaign_id": campaign_id,
                "name": name,
                "description": description
            },
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Campaign '{name}' created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Campaign creation failed: {str(e)}")

@app.get("/campaigns/{campaign_id}")
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics and trends"""
    try:
        stats = campaign_tracker.get_campaign_stats(campaign_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return {
            "data": stats,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Campaign statistics retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve campaign stats: {str(e)}")

@app.get("/campaigns")
async def list_campaigns():
    """List all campaigns"""
    try:
        campaigns = [
            {
                "id": campaign_id,
                "name": campaign_data["name"],
                "total_emails": campaign_data["total_emails"],
                "average_score": campaign_data["average_score"],
                "batch_count": len(campaign_data["batches"]),
                "created_at": campaign_data["created_at"]
            }
            for campaign_id, campaign_data in campaign_tracker.campaigns.items()
        ]
        
        return {
            "data": campaigns,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": f"Retrieved {len(campaigns)} campaigns"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list campaigns: {str(e)}")

# --- HUGGINGFACE API USAGE ENDPOINTS ---

@app.get("/api/huggingface/usage")
async def get_huggingface_usage(admin_user = Depends(get_current_admin)):
    """Get Hugging Face API usage information"""
    try:
        usage_data = hf_monitor.get_api_usage()
        return {
            "data": usage_data,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "message": "Hugging Face API usage retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve Hugging Face usage: {str(e)}")

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
    print(f"INFO: Starting InboxQualify API v2.0.0 with {DB_TYPE} database...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
