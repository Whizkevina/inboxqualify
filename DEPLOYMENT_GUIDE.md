# 🚀 Production Deployment Guide

## Frontend (Netlify) + Backend (Render) Setup

### 🔧 **STEP 1: Configure Your Backend URL**

1. **Get your Render backend URL** from your Render dashboard
   - It should look like: `https://your-app-name.onrender.com`

2. **Update the frontend configuration:**
   - Open `js/config.js`
   - Replace `your-render-app-name` with your actual Render app name:
   ```javascript
   return 'https://your-actual-render-app-name.onrender.com';
   ```

### 🔧 **STEP 2: Render Backend Configuration**

#### Environment Variables on Render:
Set these in your Render dashboard:
```
ADMIN_USERNAME=your_secure_username
ADMIN_PASSWORD=your_secure_password
HUGGINGFACE_API_KEY=your_hf_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_key
```

#### Build & Start Commands:
```bash
# Build Command:
pip install -r requirements.txt

# Start Command:
python main_supabase.py
```

### 🔧 **STEP 3: CORS Configuration**

Make sure your backend allows requests from your Netlify domain. In `main_supabase.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000", 
        "https://inboxqualify.netlify.app/",  # Add your actual Netlify URL
        # "https://your-custom-domain.com"  # If you have a custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 🔧 **STEP 4: Netlify Configuration**

Create a `_redirects` file in your root directory:
```
# API redirect for SPA
/*    /index.html   200
```

### 🔧 **STEP 5: Test the Setup**

1. **Deploy to Netlify:**
   - Connect your GitHub repo to Netlify
   - Deploy from the main branch

2. **Deploy to Render:**
   - Connect your GitHub repo to Render
   - Use `main_supabase.py` as the start command

3. **Test API Connection:**
   - Open browser console on your Netlify site
   - Check for CORS errors
   - Verify API calls are reaching Render

### 🚨 **Common Issues & Fixes**

#### Issue: "CORS Error"
**Fix:** Add your Netlify URL to CORS origins in `main_supabase.py`

#### Issue: "API calls return HTML instead of JSON"
**Fix:** Ensure you're running `main_supabase.py`, not `main.py`

#### Issue: "Templates not loading"
**Fix:** Check that your Render URL is correctly configured in `js/config.js`

#### Issue: "500 Internal Server Error"
**Fix:** Check Render logs for missing environment variables

### 📋 **Production Checklist**

- ✅ Backend deployed to Render with `main_supabase.py`
- ✅ All environment variables set on Render
- ✅ Frontend deployed to Netlify
- ✅ `js/config.js` updated with correct Render URL
- ✅ CORS configured with Netlify domain
- ✅ Templates page loads without errors
- ✅ All API endpoints working

### 🔍 **Testing Your Deployment**

1. Visit your Netlify URL
2. Open browser DevTools → Console
3. Navigate to Templates page
4. Should see logs like:
   ```
   Starting to load templates...
   API URL: https://your-render-app.onrender.com/api/templates
   Response received: Response
   Response status: 200
   ```

If you see these logs, your deployment is working correctly! 🎉

---

## Quick Fix Commands

```bash
# Update config with your Render URL
# Edit js/config.js and replace:
return 'https://your-actual-render-app-name.onrender.com';

# Commit and push to trigger deployment
git add .
git commit -m "Configure production API endpoints"
git push origin main
```
