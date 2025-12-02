"""
Comprehensive health check service
"""
import time
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import text
from app.core.database import engine
from app.core.mongodb import get_mongodb_database
from app.core.redis_client import get_redis_client
from app.core.config import settings


class HealthCheckService:
    """Service for comprehensive health checks"""
    
    def __init__(self):
        self.checks: List[Dict] = []
    
    def check_postgresql(self) -> Dict:
        """Check PostgreSQL connectivity and performance"""
        check_result = {
            "service": "postgresql",
            "status": "unknown",
            "response_time_ms": 0,
            "details": {},
        }
        
        start_time = time.time()
        try:
            with engine.connect() as conn:
                # Basic connectivity
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Check connection pool
                pool = engine.pool
                check_result["details"] = {
                    "pool_size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }
                
                # Check database version
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                check_result["details"]["version"] = version.split(",")[0] if version else "unknown"
                
                response_time = (time.time() - start_time) * 1000
                check_result["status"] = "healthy"
                check_result["response_time_ms"] = round(response_time, 2)
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "unhealthy"
            check_result["response_time_ms"] = round(response_time, 2)
            check_result["error"] = str(e)
        
        return check_result
    
    def check_mongodb(self) -> Dict:
        """Check MongoDB connectivity and performance"""
        check_result = {
            "service": "mongodb",
            "status": "unknown",
            "response_time_ms": 0,
            "details": {},
        }
        
        start_time = time.time()
        try:
            mongodb = get_mongodb_database()
            
            # Ping command
            ping_result = mongodb.admin.command("ping")
            
            # Get server info
            server_info = mongodb.client.server_info()
            
            check_result["details"] = {
                "version": server_info.get("version", "unknown"),
                "uptime": server_info.get("uptime", 0),
            }
            
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "healthy"
            check_result["response_time_ms"] = round(response_time, 2)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "unhealthy"
            check_result["response_time_ms"] = round(response_time, 2)
            check_result["error"] = str(e)
        
        return check_result
    
    def check_redis(self) -> Dict:
        """Check Redis connectivity and performance"""
        check_result = {
            "service": "redis",
            "status": "unknown",
            "response_time_ms": 0,
            "details": {},
        }
        
        start_time = time.time()
        try:
            redis_client = get_redis_client()
            
            # Ping
            redis_client.ping()
            
            # Get info
            info = redis_client.info()
            
            check_result["details"] = {
                "version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace": info.get("db0", {}),
            }
            
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "healthy"
            check_result["response_time_ms"] = round(response_time, 2)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "unhealthy"
            check_result["response_time_ms"] = round(response_time, 2)
            check_result["error"] = str(e)
        
        return check_result
    
    def check_cache(self) -> Dict:
        """Check cache functionality"""
        check_result = {
            "service": "cache",
            "status": "unknown",
            "response_time_ms": 0,
            "details": {},
        }
        
        start_time = time.time()
        try:
            from app.core.cache import CacheManager
            
            cache_manager = CacheManager()
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": time.time()}
            
            # Test set
            cache_manager.set(test_key, test_value, ttl=10)
            
            # Test get
            cached_value = cache_manager.get(test_key)
            
            if cached_value and cached_value.get("test"):
                # Clean up
                cache_manager.delete(test_key)
                
                response_time = (time.time() - start_time) * 1000
                check_result["status"] = "healthy"
                check_result["response_time_ms"] = round(response_time, 2)
            else:
                check_result["status"] = "unhealthy"
                check_result["error"] = "Cache read/write test failed"
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            check_result["status"] = "unhealthy"
            check_result["response_time_ms"] = round(response_time, 2)
            check_result["error"] = str(e)
        
        return check_result
    
    def check_disk_space(self) -> Dict:
        """Check disk space availability"""
        check_result = {
            "service": "disk",
            "status": "unknown",
            "details": {},
        }
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage("/")
            
            check_result["details"] = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "percent_free": round((free / total) * 100, 2),
            }
            
            # Consider unhealthy if less than 10% free
            if (free / total) < 0.1:
                check_result["status"] = "unhealthy"
                check_result["warning"] = "Low disk space"
            else:
                check_result["status"] = "healthy"
                
        except Exception as e:
            check_result["status"] = "unknown"
            check_result["error"] = str(e)
        
        return check_result
    
    def get_comprehensive_health(self, include_disk: bool = False) -> Dict:
        """Get comprehensive health status"""
        overall_start = time.time()
        
        # Run all checks
        checks = {
            "postgresql": self.check_postgresql(),
            "mongodb": self.check_mongodb(),
            "redis": self.check_redis(),
            "cache": self.check_cache(),
        }
        
        if include_disk:
            checks["disk"] = self.check_disk_space()
        
        # Determine overall status
        all_healthy = all(
            check["status"] == "healthy" 
            for check in checks.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Calculate total response time
        total_time = (time.time() - overall_start) * 1000
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "version": settings.APP_VERSION,
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy": sum(1 for c in checks.values() if c["status"] == "healthy"),
                "unhealthy": sum(1 for c in checks.values() if c["status"] == "unhealthy"),
                "total_response_time_ms": round(total_time, 2),
            },
        }
    
    def get_liveness(self) -> Dict:
        """Liveness probe - is the application running?"""
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_readiness(self) -> Dict:
        """Readiness probe - is the application ready to serve traffic?"""
        # Check critical services only
        postgresql = self.check_postgresql()
        mongodb = self.check_mongodb()
        redis = self.check_redis()
        
        # Application is ready if all critical services are healthy
        ready = all(
            check["status"] == "healthy"
            for check in [postgresql, mongodb, redis]
        )
        
        return {
            "status": "ready" if ready else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "postgresql": postgresql["status"],
                "mongodb": mongodb["status"],
                "redis": redis["status"],
            },
        }

