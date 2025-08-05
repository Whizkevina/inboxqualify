"""
Admin Users Setup Script for Supabase
Creates admin users for InboxQualify dashboard access
"""

import os
from dotenv import load_dotenv
from supabase_db import get_db

def create_admin_users():
    """Create admin users in Supabase database"""
    
    print("👥 InboxQualify Admin Users Setup")
    print("=" * 40)
    
    try:
        # Initialize Supabase database
        db = get_db()
        print("✅ Connected to Supabase database")
        
        # Create primary admin user (from environment)
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL")
        
        if not admin_username or not admin_password:
            print("❌ Error: ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables!")
            return False
        
        print(f"\n🔧 Creating primary admin user: {admin_username}")
        
        success = db.create_admin_user(
            username=admin_username,
            password=admin_password,
            email=admin_email or "admin@inboxqualify.com",
            role="admin"
        )
        
        if success:
            print(f"✅ Admin user '{admin_username}' created successfully!")
        else:
            print(f"⚠️ Admin user '{admin_username}' may already exist or creation failed")
            
        # NOTE: Additional default admin users removed for security
        # Add any additional users through the admin interface or environment variables
        
        # List all admin users
        print("\n📋 Current admin users in database:")
        users = db.get_admin_users()
        
        if users:
            for user in users:
                status = "🟢 Active" if user.get('is_active', True) else "🔴 Inactive"
                last_login = user.get('last_login', 'Never')[:19] if user.get('last_login') else 'Never'
                print(f"  • {user['username']} ({user['role']}) - {status} - Last login: {last_login}")
        else:
            print("  No admin users found")
        
        # Test authentication only with environment user
        print("\n🧪 Testing authentication...")
        
        if admin_username and admin_password:
            test_user = db.verify_admin_user(admin_username, admin_password)
            if test_user:
                print(f"✅ Authentication successful for '{admin_username}' (role: {test_user.get('role', 'unknown')})")
            else:
                print(f"❌ Authentication failed for '{admin_username}'")
        
        print("\n" + "=" * 40)
        print("🎉 Admin users setup complete!")
        print("\n📝 NOTE: Admin credentials are configured via environment variables")
        print("🔗 Access dashboard: http://localhost:8000/admin")
        
    except Exception as e:
        print(f"❌ Error setting up admin users: {e}")
        print("💡 Make sure Supabase is properly configured and tables exist")

if __name__ == "__main__":
    load_dotenv()
    create_admin_users()
