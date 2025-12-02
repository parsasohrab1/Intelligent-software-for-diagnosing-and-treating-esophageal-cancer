"""
Script to create admin user
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security.auth import get_password_hash
from app.core.security.rbac import Role


def create_admin_user(username: str, email: str, password: str):
    """Create an admin user"""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User {username} already exists!")
            return

        # Create admin user
        hashed_password = get_password_hash(password)
        admin_user = User(
            user_id=f"admin_{username}",
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name="System Administrator",
            role=Role.SYSTEM_ADMINISTRATOR,
            is_active=True,
            is_superuser=True,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: {admin_user.role.value}")

    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--username", type=str, default="admin", help="Username")
    parser.add_argument("--email", type=str, default="admin@inescape.com", help="Email")
    parser.add_argument("--password", type=str, required=True, help="Password")

    args = parser.parse_args()

    create_admin_user(args.username, args.email, args.password)

