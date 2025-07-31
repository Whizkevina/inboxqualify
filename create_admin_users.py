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
        admin_username = os.getenv("ADMIN_USERNAME", "timmie").strip("'\"")
        admin_password = os.getenv("ADMIN_PASSWORD", "qualify321").strip("'\"")
        admin_email = os.getenv("ADMIN_EMAIL", "timmyondbeat@gmail.com")
        
        print(f"\n🔧 Creating primary admin user: {admin_username}")
        
        success = db.create_admin_user(
            username=admin_username,
            password=admin_password,
            email=admin_email,
            role="admin"
        )
        
        if success:
            print(f"✅ Admin user '{admin_username}' created successfully!")
        else:
            print(f"⚠️ Admin user '{admin_username}' may already exist or creation failed")
        
        # Create additional admin users
        additional_users = [
            {
                "username": "admin",
                "password": "admin123",
                "email": "admin@inboxqualify.com",
                "role": "admin"
            },
            {
                "username": "viewer",
                "password": "viewer123", 
                "email": "viewer@inboxqualify.com",
                "role": "viewer"
            }
        ]
        
        print("\n🔧 Creating additional admin users...")
        for user in additional_users:
            success = db.create_admin_user(
                username=user["username"],
                password=user["password"],
                email=user["email"],
                role=user["role"]
            )
            
            if success:
                print(f"✅ {user['role'].title()} user '{user['username']}' created successfully!")
            else:
                print(f"⚠️ User '{user['username']}' may already exist or creation failed")
        
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
        
        # Test authentication
        print("\n🧪 Testing authentication...")
        
        test_users = [
            (admin_username, admin_password),
            ("admin", "admin123"),
            ("viewer", "viewer123")
        ]
        
        for username, password in test_users:
            user = db.verify_admin_user(username, password)
            if user:
                print(f"✅ Authentication successful for '{username}' (role: {user.get('role', 'unknown')})")
            else:
                print(f"❌ Authentication failed for '{username}'")
        
        print("\n" + "=" * 40)
        print("🎉 Admin users setup complete!")
        print("\n📝 Login credentials:")
        print(f"  Primary Admin: {admin_username} / {admin_password}")
        print("  Secondary Admin: admin / admin123")
        print("  Viewer User: viewer / viewer123")
        print("\n🔗 Access dashboard: http://localhost:8000/admin")
        
    except Exception as e:
        print(f"❌ Error setting up admin users: {e}")
        print("💡 Make sure Supabase is properly configured and tables exist")

if __name__ == "__main__":
    load_dotenv()
    create_admin_users()
