# 🔧 Troubleshooting Guide

## Production Deployment: Templates Page Shows "Error loading templates" 

### Problem (Production - Netlify + Render)
When visiting the Templates page on your live site, you see this error in the browser console:
```
SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

### Root Cause
Your frontend (Netlify) is trying to call API endpoints on its own domain instead of your Render backend.

### Solution

1. **Update your Render backend URL in the frontend:**
   - Open `js/config.js`
   - Replace `your-render-app-name` with your actual Render app name:
   ```javascript
   return 'https://your-actual-render-app-name.onrender.com';
   ```

2. **Ensure CORS is configured properly in `main_supabase.py`:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",
           "http://localhost:8000", 
           "https://your-netlify-app.netlify.app",  # Your actual Netlify URL
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Verify your Render deployment:**
   - Ensure you're running `main_supabase.py` (not `main.py`)
   - Check that all environment variables are set on Render

4. **Test the API directly:**
   - Visit: `https://your-render-app.onrender.com/api/templates`
   - Should return JSON data, not HTML

---

## Local Development: Templates Page Shows "Error loading templates"

### Problem
When running locally, you see this error in the browser console:
```
SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

### Root Cause
You're running the wrong server file. The templates functionality is only available in `main_supabase.py`, not in `main.py`.

### Solution

1. **Stop the current server** (if running):
   ```bash
   Ctrl+C  # In the terminal where the server is running
   ```

2. **Make sure you have the environment variables set up**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see SECURITY_SETUP.md)
   ```

3. **Run the correct server file**:
   ```bash
   python main_supabase.py
   ```

4. **Verify it's working**:
   - Open your browser to `http://localhost:8000`
   - Navigate to Templates page
   - Check that templates load properly

### How to Tell Which Server You're Running

**Correct Server (main_supabase.py):**
- Console shows: "Starting InboxQualify API v2.0.0 with supabase database..."
- Templates page loads email templates
- All Quick Wins features work

**Wrong Server (main.py):**
- Console shows different startup message
- Templates page shows JSON parsing errors
- Some features may not work

### Additional Features Only in main_supabase.py

- ✅ Email Templates & AI Suggestions
- ✅ Batch Email Analysis (CSV upload)
- ✅ Email Rewriter with AI
- ✅ Campaign Tracking
- ✅ Enhanced Admin Dashboard
- ✅ Quick Wins Features (Character Counters, Dark Mode, etc.)

### Still Having Issues?

1. **Check your .env file** has the required variables:
   ```
   ADMIN_USERNAME=your_username
   ADMIN_PASSWORD=your_password
   HUGGINGFACE_API_KEY=your_hf_key (optional)
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check the console output** when starting the server for any error messages.

4. **Ensure port 8000 is available** (not used by another process).

---

## Quick Start Commands

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies  
pip install -r requirements.txt

# 3. Run the correct server
python main_supabase.py

# 4. Open browser
# http://localhost:8000
```

That's it! The templates should now load properly. 🎉
