"""
Script to create initial database migration
ایجاد migration اولیه برای تمام جداول
"""
import os
import sys
import subprocess

def main():
    """Create initial migration"""
    print("=" * 60)
    print("Creating Initial Database Migration")
    print("=" * 60)
    
    # Check if alembic is installed
    try:
        import alembic
    except ImportError:
        print("❌ Error: Alembic is not installed")
        print("Install with: pip install alembic")
        sys.exit(1)
    
    # Create migration
    print("\n📝 Creating migration...")
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial migration: Create all tables"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print(result.stdout)
        else:
            print("❌ Error creating migration:")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Review the migration file in alembic/versions/")
    print("2. Run: alembic upgrade head")
    print("=" * 60)

if __name__ == "__main__":
    main()

