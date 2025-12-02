"""
Development environment setup script
"""
import sys
import os
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(
            ["docker", "ps"], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def start_services():
    """Start Docker services"""
    print("Starting Docker services...")
    try:
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        print("✅ Docker services started")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting services: {e}")
        return False
    except FileNotFoundError:
        print("❌ docker-compose not found. Please install Docker Compose.")
        return False


def wait_for_services(max_wait=60):
    """Wait for services to be ready"""
    print("Waiting for services to be ready...")
    from app.core.database import engine
    from app.core.mongodb import get_mongodb_database
    from app.core.redis_client import get_redis_client

    start_time = time.time()
    services_ready = {"postgres": False, "mongodb": False, "redis": False}

    while time.time() - start_time < max_wait:
        # Check PostgreSQL
        if not services_ready["postgres"]:
            try:
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                services_ready["postgres"] = True
                print("  ✅ PostgreSQL is ready")
            except:
                pass

        # Check MongoDB
        if not services_ready["mongodb"]:
            try:
                db = get_mongodb_database()
                db.admin.command("ping")
                services_ready["mongodb"] = True
                print("  ✅ MongoDB is ready")
            except:
                pass

        # Check Redis
        if not services_ready["redis"]:
            try:
                redis = get_redis_client()
                redis.ping()
                services_ready["redis"] = True
                print("  ✅ Redis is ready")
            except:
                pass

        if all(services_ready.values()):
            print("✅ All services are ready!")
            return True

        time.sleep(2)

    print("⚠️  Some services may not be ready yet")
    return False


def initialize_database():
    """Initialize database"""
    print("\nInitializing database...")
    try:
        from scripts.init_database import main as init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


def create_admin_user():
    """Create admin user"""
    print("\nCreating admin user...")
    import sys
    sys.argv = [
        "create_admin_user.py",
        "--username", "admin",
        "--email", "admin@example.com",
        "--password", "admin123"
    ]
    try:
        from scripts.create_admin_user import create_admin_user
        create_admin_user("admin", "admin@example.com", "admin123")
        print("✅ Admin user created")
        print("   Username: admin")
        print("   Password: admin123")
        return True
    except Exception as e:
        print(f"⚠️  Admin user may already exist: {e}")
        return True  # Not critical if user exists


def main():
    """Main setup function"""
    print("=" * 60)
    print("INEsCape Development Environment Setup")
    print("=" * 60)

    # Check Docker
    if not check_docker():
        print("❌ Docker is not running. Please start Docker Desktop.")
        return False

    # Start services
    if not start_services():
        return False

    # Wait for services
    if not wait_for_services():
        print("⚠️  Continuing anyway...")

    # Initialize database
    if not initialize_database():
        print("⚠️  Database initialization failed, but continuing...")

    # Create admin user
    create_admin_user()

    print("\n" + "=" * 60)
    print("✅ Development environment is ready!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the server: python scripts/run_server.py")
    print("2. Access API docs: http://localhost:8000/docs")
    print("3. Login with: admin / admin123")
    print("\n" + "=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

