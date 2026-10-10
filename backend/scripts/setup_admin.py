import sys
import os
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

def setup_admin():
    """Create new admin account and remove old admin"""
    db = SessionLocal()
    try:
        # Remove old admin
        old_admin_email = 'propnoxa_admin@example.com'
        old_admin = db.query(User).filter(User.email == old_admin_email).first()
        if old_admin:
            db.delete(old_admin)
            db.commit()
            print(f"Removed old admin: {old_admin_email}")
        else:
            print(f"Old admin not found: {old_admin_email}")

        # Create new admin
        new_admin_email = 'kebirogabriel@gmail.com'
        new_admin_password = 'onsomuRiley2022'
        new_admin_name = 'Gabriel Onsomu'
        
        # Check if new admin already exists
        existing_admin = db.query(User).filter(User.email == new_admin_email).first()
        if existing_admin:
            # Update to admin role
            existing_admin.role = 'admin'
            existing_admin.full_name = new_admin_name
            existing_admin.hashed_password = get_password_hash(new_admin_password)
            db.add(existing_admin)
            db.commit()
            print(f"Updated existing user to admin: {new_admin_email}")
        else:
            # Create new admin
            hashed_password = get_password_hash(new_admin_password)
            new_admin = User(
                email=new_admin_email,
                hashed_password=hashed_password,
                full_name=new_admin_name,
                role='admin',
                roles_csv='admin,manager,owner,agent,tenant,service_provider',
                is_active=True,
                is_verified=True
            )
            db.add(new_admin)
            db.commit()
            print(f"Created new admin account: {new_admin_email}")
        
        print(f"Admin setup complete!")
        print(f"   Email: {new_admin_email}")
        print(f"   Name: {new_admin_name}")
        print(f"   (Password has been set and will not be displayed)")
        
    except Exception as e:
        db.rollback()
        print(f"Error setting up admin: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    setup_admin()