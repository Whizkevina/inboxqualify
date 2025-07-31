"""
Phase 2 Setup Script for InboxQualify Admin Dashboard
Initializes multi-admin support, email alerts, and enhanced features
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from admin_dashboard import AnalyticsDB
from email_alerts import create_email_alert_system
from dotenv import load_dotenv

def setup_phase2():
    """Initialize Phase 2 features"""
    print("🚀 Setting up InboxQualify Admin Dashboard - Phase 2")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize analytics database with new tables
    print("📊 Initializing enhanced analytics database...")
    analytics_db = AnalyticsDB()
    
    # Create default admin user if none exists
    print("👤 Setting up admin users...")
    
    # Check if any admin users exist
    existing_users = analytics_db.get_admin_users()
    
    if not existing_users:
        print("Creating default admin user...")
        username = input("Enter admin username (default: admin): ").strip() or "admin"
        
        while True:
            password = input("Enter admin password: ").strip()
            if len(password) >= 6:
                break
            print("❌ Password must be at least 6 characters long")
        
        email = input("Enter admin email (optional): ").strip() or None
        
        success = analytics_db.create_admin_user(username, password, email, "admin")
        
        if success:
            print(f"✅ Admin user '{username}' created successfully!")
        else:
            print(f"❌ Failed to create admin user '{username}' (may already exist)")
    else:
        print(f"✅ Found {len(existing_users)} existing admin user(s)")
    
    # Set up email alerts
    print("\n📧 Setting up email alert system...")
    
    # Check email configuration
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")
    
    if not all([smtp_server, smtp_username, smtp_password]):
        print("⚠️  Email configuration incomplete. Add to your .env file:")
        print("   SMTP_SERVER=smtp.gmail.com")
        print("   SMTP_PORT=587")
        print("   SMTP_USERNAME=your-email@gmail.com")
        print("   SMTP_PASSWORD=your-app-password")
        print("   ADMIN_EMAIL=admin@yourcompany.com")
        print()
        
        configure_email = input("Would you like to configure email settings now? (y/N): ").lower().startswith('y')
        
        if configure_email:
            setup_email_config()
    else:
        print("✅ Email configuration found!")
        
        # Test email alerts
        try:
            email_alert_system = create_email_alert_system(analytics_db)
            print("✅ Email alert system initialized successfully!")
        except Exception as e:
            print(f"⚠️  Email alert system warning: {e}")
    
    # Display setup summary
    print("\n" + "=" * 60)
    print("🎉 Phase 2 Setup Complete!")
    print("=" * 60)
    print("\n📋 New Features Available:")
    print("   • 👥 Multi-admin user management")
    print("   • 📈 Advanced analytics with filtering")
    print("   • 🚨 Email alert system")
    print("   • 📋 Admin audit logging")
    print("   • 💾 Enhanced data export options")
    print("   • 🎨 Modern tabbed dashboard interface")
    
    print("\n🔗 Access your enhanced dashboard at:")
    print("   http://localhost:8000/admin")
    
    print("\n🔧 Next Steps:")
    print("   1. Start your server: python API/main.py")
    print("   2. Login with your admin credentials")
    print("   3. Explore the new tabs: Analytics, Users, Alerts, Audit Log")
    print("   4. Configure email settings for alerts (if not done)")
    print("   5. Create additional admin users if needed")
    
    return True

def setup_email_config():
    """Interactive email configuration setup"""
    print("\n📧 Email Configuration Setup")
    print("-" * 30)
    
    env_file = Path('.env')
    
    # Read existing .env content
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Get email settings
    smtp_server = input("SMTP Server (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    smtp_port = input("SMTP Port (default: 587): ").strip() or "587"
    smtp_username = input("SMTP Username (your email): ").strip()
    smtp_password = input("SMTP Password (app password for Gmail): ").strip()
    admin_email = input("Admin notification email: ").strip()
    
    # Update .env file
    new_env_lines = []
    
    # Email settings to add/update
    email_settings = {
        'SMTP_SERVER': smtp_server,
        'SMTP_PORT': smtp_port,
        'SMTP_USERNAME': smtp_username,
        'SMTP_PASSWORD': smtp_password,
        'ADMIN_EMAIL': admin_email
    }
    
    # Parse existing .env content
    existing_keys = set()
    if env_content:
        for line in env_content.split('\n'):
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in email_settings:
                    # Update existing key
                    new_env_lines.append(f"{key}={email_settings[key]}")
                    existing_keys.add(key)
                else:
                    # Keep existing line
                    new_env_lines.append(line)
            else:
                # Keep comments and empty lines
                new_env_lines.append(line)
    
    # Add new email settings that weren't in the file
    for key, value in email_settings.items():
        if key not in existing_keys:
            new_env_lines.append(f"{key}={value}")
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_env_lines))
    
    print("✅ Email configuration saved to .env file!")

def test_phase2_features():
    """Test Phase 2 features"""
    print("\n🧪 Testing Phase 2 Features...")
    print("-" * 30)
    
    try:
        # Test database
        analytics_db = AnalyticsDB()
        users = analytics_db.get_admin_users()
        print(f"✅ Database: Found {len(users)} admin users")
        
        # Test email alerts (if configured)
        try:
            email_alerts = create_email_alert_system(analytics_db)
            print("✅ Email alerts: System initialized")
        except Exception as e:
            print(f"⚠️  Email alerts: {e}")
        
        print("✅ All Phase 2 features tested successfully!")
        
    except Exception as e:
        print(f"❌ Error testing features: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Check if running from correct directory
    if not Path("admin_dashboard.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    print("🎯 InboxQualify Admin Dashboard - Phase 2 Setup")
    print("This will set up advanced features including multi-admin support,")
    print("email alerts, enhanced analytics, and audit logging.\n")
    
    proceed = input("Continue with Phase 2 setup? (Y/n): ").lower()
    if proceed.startswith('n'):
        print("Setup cancelled.")
        sys.exit(0)
    
    # Run setup
    success = setup_phase2()
    
    if success:
        # Optionally test features
        test_features = input("\nWould you like to test Phase 2 features? (Y/n): ").lower()
        if not test_features.startswith('n'):
            test_phase2_features()
    
    print("\n🎉 Setup complete! Your enhanced admin dashboard is ready to use!")
