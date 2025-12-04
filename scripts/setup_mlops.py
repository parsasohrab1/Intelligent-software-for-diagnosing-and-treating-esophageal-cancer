"""
Setup script for MLOps features
Installs dependencies and verifies configuration
"""
import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing MLOps dependencies...")
    
    dependencies = [
        "pika==1.3.2",
        "kafka-python==2.0.2",
        "pydicom==2.4.4",
        "nibabel==5.2.1",
        "opencv-python==4.8.1.78",
        "Pillow==10.1.0",
    ]
    
    for dep in dependencies:
        try:
            print(f"  Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  ✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️  Failed to install {dep}")
    
    print("✅ Dependencies installed")


def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(["docker", "ps"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is running")
            return True
        else:
            print("⚠️  Docker is not running")
            return False
    except FileNotFoundError:
        print("⚠️  Docker is not installed")
        return False


def check_services():
    """Check if required services are running"""
    print("\n🔍 Checking services...")
    
    services = {
        "MongoDB": ("localhost", 27017),
        "RabbitMQ": ("localhost", 5672),
        "Kafka": ("localhost", 9092),
    }
    
    import socket
    
    for service_name, (host, port) in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"  ✅ {service_name} is running on {host}:{port}")
            else:
                print(f"  ⚠️  {service_name} is not running on {host}:{port}")
        except Exception as e:
            print(f"  ⚠️  Could not check {service_name}: {str(e)}")


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        print("📝 Creating .env file from .env.example...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ .env file created")
        print("⚠️  Please review and update .env file with your settings")
    else:
        print("⚠️  .env.example not found, skipping .env creation")


def verify_imports():
    """Verify that all required modules can be imported"""
    print("\n🔍 Verifying imports...")
    
    modules = [
        ("pika", "RabbitMQ client"),
        ("kafka", "Kafka client"),
        ("pydicom", "DICOM processing"),
        ("nibabel", "NIfTI processing"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
    ]
    
    for module_name, description in modules:
        try:
            if module_name == "cv2":
                __import__("cv2")
            elif module_name == "PIL":
                __import__("PIL")
            else:
                __import__(module_name)
            print(f"  ✅ {module_name} ({description})")
        except ImportError:
            print(f"  ⚠️  {module_name} not installed ({description})")


def main():
    """Main setup function"""
    print("=" * 50)
    print("MLOps Features Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Check Docker
    docker_running = check_docker()
    
    # Create .env file
    create_env_file()
    
    # Verify imports
    verify_imports()
    
    # Check services (if Docker is running)
    if docker_running:
        check_services()
    
    print("\n" + "=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("1. Review and update .env file if needed")
    print("2. Start services: docker-compose up -d rabbitmq kafka mongodb")
    print("3. Wait for services to be ready (30-60 seconds)")
    print("4. Start the application: python scripts/run_server.py")
    print("\n📚 Documentation: docs/MLOPS_FEATURES.md")


if __name__ == "__main__":
    main()

