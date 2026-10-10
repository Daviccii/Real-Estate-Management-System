import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.models.user import User

def check_admin():
    """Check if admin user exists in database"""
    db = SessionLocal()
    try:
        admin_email = 'kebirogabriel@gmail.com'
        admin = db.query(User).filter(User.email == admin_email).first()
        
        if admin:
            print(f"Admin user found:")
            print(f"  Email: {admin.email}")
            print(f"  Name: {admin.full_name}")
            print(f"  Role: {admin.role}")
            print(f"  Active: {admin.is_active}")
            print(f"  ID: {admin.id}")
        else:
            print(f"Admin user NOT found: {admin_email}")
            
        # Show all users
        all_users = db.query(User).all()
        print(f"\nTotal users in database: {len(all_users)}")
        for user in all_users:
            print(f"  - {user.email} (Role: {user.role}, Active: {user.is_active})")
            
    except Exception as e:
        print(f"Error checking admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_admin()