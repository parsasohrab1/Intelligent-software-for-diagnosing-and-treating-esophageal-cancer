"""
Go-live checklist verification script
"""
import sys
import os
import requests
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GoLiveChecker:
    """Verify go-live readiness"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.checks: List[Tuple[str, bool, str]] = []

    def check_health(self) -> bool:
        """Check system health"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                self.checks.append(("Health Check", True, "System is healthy"))
                return True
            else:
                self.checks.append(
                    ("Health Check", False, f"Status code: {response.status_code}")
                )
                return False
        except Exception as e:
            self.checks.append(("Health Check", False, str(e)))
            return False

    def check_database(self) -> bool:
        """Check database connectivity"""
        try:
            from app.core.database import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            self.checks.append(("Database Connection", True, "Connected"))
            return True
        except Exception as e:
            self.checks.append(("Database Connection", False, str(e)))
            return False

    def check_mongodb(self) -> bool:
        """Check MongoDB connectivity"""
        try:
            from app.core.mongodb import get_mongodb_database
            db = get_mongodb_database()
            db.admin.command("ping")
            self.checks.append(("MongoDB Connection", True, "Connected"))
            return True
        except Exception as e:
            self.checks.append(("MongoDB Connection", False, str(e)))
            return False

    def check_redis(self) -> bool:
        """Check Redis connectivity"""
        try:
            from app.core.redis_client import get_redis_client
            redis = get_redis_client()
            redis.ping()
            self.checks.append(("Redis Connection", True, "Connected"))
            return True
        except Exception as e:
            self.checks.append(("Redis Connection", False, str(e)))
            return False

    def check_api_docs(self) -> bool:
        """Check API documentation availability"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                self.checks.append(("API Documentation", True, "Available"))
                return True
            else:
                self.checks.append(
                    ("API Documentation", False, f"Status: {response.status_code}")
                )
                return False
        except Exception as e:
            self.checks.append(("API Documentation", False, str(e)))
            return False

    def check_environment_variables(self) -> bool:
        """Check critical environment variables"""
        from app.core.config import settings

        critical_vars = ["SECRET_KEY", "POSTGRES_PASSWORD"]
        missing = []

        for var in critical_vars:
            value = getattr(settings, var, None)
            if not value or value == "your-secret-key-change-in-production":
                missing.append(var)

        if missing:
            self.checks.append(
                (
                    "Environment Variables",
                    False,
                    f"Missing or default: {', '.join(missing)}",
                )
            )
            return False
        else:
            self.checks.append(("Environment Variables", True, "All set"))
            return True

    def run_all_checks(self) -> Dict:
        """Run all checks"""
        print("Running go-live checks...\n")

        results = {
            "health": self.check_health(),
            "database": self.check_database(),
            "mongodb": self.check_mongodb(),
            "redis": self.check_redis(),
            "api_docs": self.check_api_docs(),
            "env_vars": self.check_environment_variables(),
        }

        return results

    def print_report(self):
        """Print check report"""
        print("\n" + "=" * 60)
        print("Go-Live Checklist Report")
        print("=" * 60)

        passed = sum(1 for _, status, _ in self.checks if status)
        total = len(self.checks)

        for check_name, status, message in self.checks:
            status_symbol = "[OK]" if status else "[FAIL]"
            print(f"{status_symbol} {check_name}: {message}")

        print("\n" + "=" * 60)
        print(f"Results: {passed}/{total} checks passed")
        print("=" * 60)

        if passed == total:
            print("\n[SUCCESS] System is ready for go-live!")
        else:
            print("\n[WARNING] System is NOT ready. Please fix the issues above.")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Go-live checklist verification")
    parser.add_argument(
        "--url", type=str, default="http://localhost:8000", help="Base URL"
    )

    args = parser.parse_args()

    checker = GoLiveChecker(base_url=args.url)
    checker.run_all_checks()
    checker.print_report()


if __name__ == "__main__":
    main()

