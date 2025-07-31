"""
Supabase Setup Script for InboxQualify
Automated setup with environment variable templates
"""

import os
from dotenv import load_dotenv

def create_supabase_setup():
    """Create Supabase setup instructions and templates"""
    
    print("🚀 InboxQualify Supabase Migration Setup")
    print("=" * 50)
    
    # Check current .env file
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or supabase_url == 'your-project-url-here':
        print("\n📋 SETUP REQUIRED:")
        print("1. Go to https://supabase.com")
        print("2. Create a new project")
        print("3. Go to Settings > API")
        print("4. Copy your Project URL and service_role key")
        print("5. Update your .env file with:")
        print("   SUPABASE_URL=https://your-project.supabase.co")
        print("   SUPABASE_SERVICE_KEY=your-service-role-key")
        print("\n6. Run the SQL migration script in Supabase SQL Editor:")
        print("   Open: Project > SQL Editor")
        print("   Copy and paste the contents of 'supabase_migration.sql'")
        print("   Click 'Run'")
        
        # Check if migration file exists
        if os.path.exists('supabase_migration.sql'):
            print("\n✅ Migration file found: supabase_migration.sql")
        else:
            print("\n❌ Migration file missing: supabase_migration.sql")
        
        print("\n📝 After setup, restart your server to use Supabase PostgreSQL!")
    else:
        print("\n✅ Supabase credentials found in .env file")
        print(f"URL: {supabase_url}")
        print("Key: ****" + supabase_key[-4:] if supabase_key else "Not set")
        
        # Test connection
        try:
            from supabase_db import get_db
            db = get_db()
            health = db.health_check()
            if health['status'] == 'healthy':
                print("✅ Supabase connection successful!")
                print("🎉 Your InboxQualify is ready to use Supabase PostgreSQL")
            else:
                print(f"❌ Connection failed: {health.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print("📋 Please run the SQL migration in Supabase SQL Editor")
    
    print("\n" + "=" * 50)
    print("🔗 Helpful Links:")
    print("   Supabase Dashboard: https://supabase.com/dashboard")
    print("   Documentation: https://supabase.com/docs")
    print("   SQL Editor: Project > SQL Editor")

if __name__ == "__main__":
    create_supabase_setup()
