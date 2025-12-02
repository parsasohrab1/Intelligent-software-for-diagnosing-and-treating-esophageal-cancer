"""
Check if required services are running
"""
import socket
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


def check_port(host, port, service_name):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"✅ {service_name} is running on {host}:{port}")
            return True
        else:
            print(f"❌ {service_name} is NOT running on {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error checking {service_name}: {str(e)}")
        return False


def main():
    """Check all required services"""
    print("Checking required services...\n")
    
    services = [
        (settings.POSTGRES_HOST, settings.POSTGRES_PORT, "PostgreSQL"),
        (settings.MONGODB_HOST, settings.MONGODB_PORT, "MongoDB"),
        (settings.REDIS_HOST, settings.REDIS_PORT, "Redis"),
    ]
    
    all_running = True
    for host, port, name in services:
        if not check_port(host, port, name):
            all_running = False
    
    print("\n" + "=" * 50)
    if all_running:
        print("✅ All services are running!")
        print("You can now run: python scripts/init_database.py")
        sys.exit(0)
    else:
        print("❌ Some services are not running!")
        print("\nTo start services, run:")
        print("  docker-compose up -d")
        print("\nOr make sure Docker Desktop is running first.")
        sys.exit(1)


if __name__ == "__main__":
    main()

