# setup_admin.py - Configure admin dashboard

import os
from dotenv import load_dotenv, set_key
import secrets
import getpass

def setup_admin_credentials():
    """Set up admin dashboard credentials"""
    
    print("🔧 InboxQualify Admin Dashboard Setup")
    print("=" * 40)
    
    # Load existing .env or create new one
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("# InboxQualify Environment Variables\n")
    
    load_dotenv(env_file)
    
    # Check if admin credentials already exist
    existing_username = os.getenv("ADMIN_USERNAME")
    existing_password = os.getenv("ADMIN_PASSWORD")
    
    if existing_username and existing_password:
        print(f"Admin credentials already exist for user: {existing_username}")
        update = input("Do you want to update them? (y/N): ").lower().strip()
        if update != 'y':
            print("Keeping existing credentials.")
            return
    
    # Get admin username
    print("\n📝 Admin Username")
    while True:
        username = input("Enter admin username (default: admin): ").strip()
        if not username:
            username = "admin"
        
        if len(username) >= 3:
            break
        print("Username must be at least 3 characters long.")
    
    # Get admin password
    print("\n🔐 Admin Password")
    while True:
        password = getpass.getpass("Enter admin password (min 8 chars): ").strip()
        if len(password) >= 8:
            confirm = getpass.getpass("Confirm password: ").strip()
            if password == confirm:
                break
            else:
                print("Passwords don't match. Try again.")
        else:
            print("Password must be at least 8 characters long.")
    
    # Save to .env file
    set_key(env_file, "ADMIN_USERNAME", username)
    set_key(env_file, "ADMIN_PASSWORD", password)
    
    print(f"\n✅ Admin credentials saved!")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"\n🌐 Access your admin dashboard at: http://localhost:8000/admin")
    print(f"📊 Or when deployed: https://yourdomain.com/admin")
    
    # Check if HF API key exists
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_key:
        print(f"\n⚠️  Warning: HUGGINGFACE_API_KEY not found in {env_file}")
        print("Add your Hugging Face API key to enable AI features:")
        print(f"HUGGINGFACE_API_KEY=your_key_here")

if __name__ == "__main__":
    try:
        setup_admin_credentials()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
