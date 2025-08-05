# 🔒 SECURITY SETUP GUIDE

## ⚠️ IMPORTANT: Complete This Setup Before Running

This guide ensures your InboxQualify installation is secure and production-ready.

## 🔑 Environment Variables Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual values:**
   ```properties
   # API Keys (Required for AI features)
   GEMINI_API_KEY=your_actual_gemini_api_key
   HUGGINGFACE_API_KEY=your_actual_hugging_face_api_key
   
   # Admin Credentials (CHANGE THESE!)
   ADMIN_USERNAME=your_secure_admin_username
   ADMIN_PASSWORD=your_secure_admin_password
   
   # Email Configuration (Optional)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_email_app_password
   ADMIN_EMAIL=your_admin_email@gmail.com
   
   # Supabase Configuration (Optional)
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   ```

## 🛡️ Security Best Practices

### Admin Credentials
- **Never use default passwords** like "admin123" or "password"
- Use strong passwords with:
  - At least 12 characters
  - Mix of uppercase, lowercase, numbers, and symbols
  - No dictionary words or personal information

### API Keys
- **Keep API keys secret** - never commit them to version control
- Get your free API keys from:
  - [Hugging Face](https://huggingface.co/settings/tokens)
  - [Google AI Studio](https://aistudio.google.com/app/apikey) (for Gemini)

### Email Configuration
- Use **app passwords** instead of your regular email password
- For Gmail: [Generate App Password](https://support.google.com/accounts/answer/185833)

## 🚀 First-Time Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (see above)

3. **Create admin user:**
   ```bash
   python create_admin_users.py
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

5. **Access the admin panel:**
   - URL: `http://localhost:8000/admin`
   - Use the credentials you set in your `.env` file

## 🔒 Production Deployment

### Additional Security Measures for Production:

1. **Use HTTPS only**
2. **Set up proper firewall rules**
3. **Use environment variables on your hosting platform**
4. **Enable rate limiting**
5. **Regular security updates**
6. **Database encryption**
7. **Backup strategies**

### Environment Variables on Different Platforms:

#### Heroku:
```bash
heroku config:set ADMIN_USERNAME=your_username
heroku config:set ADMIN_PASSWORD=your_password
heroku config:set HUGGINGFACE_API_KEY=your_key
```

#### Vercel:
Add environment variables in the Vercel dashboard under Project Settings → Environment Variables

#### Railway:
Add environment variables in the Railway dashboard under Variables

## ⚠️ NEVER COMMIT THESE FILES:
- `.env` (contains secrets)
- `*.db` (database files)
- `*.log` (log files)
- `__pycache__/` (Python cache)

## 📞 Support

If you encounter security issues:
1. Check this guide first
2. Verify your `.env` file is properly configured
3. Ensure all environment variables are set
4. Check the application logs for specific error messages

---

**Remember: Security is not optional. Always use strong, unique credentials!**
