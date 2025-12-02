"""
Unit tests for rate limiting (no database required)
"""
import pytest
import time
from app.middleware.rate_limiter import RateLimiter


class TestRateLimiterUnit:
    """Unit tests for RateLimiter class"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert limiter is not None
        assert limiter.memory_store is not None
    
    def test_rate_limit_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter()
        
        # Make requests within limit
        for i in range(5):
            allowed, count, remaining = limiter.check_rate_limit(
                identifier="test_user",
                endpoint="test_endpoint",
                max_requests=10,
                window=60
            )
            assert allowed is True
            assert count == i + 1
            assert remaining == 10 - (i + 1)
    
    def test_rate_limit_blocks_excess_requests(self):
        """Test that rate limiter blocks requests exceeding limit"""
        limiter = RateLimiter()
        
        # Make requests up to limit
        for i in range(5):
            allowed, count, remaining = limiter.check_rate_limit(
                identifier="test_user",
                endpoint="test_endpoint",
                max_requests=5,
                window=60
            )
            assert allowed is True
        
        # Next request should be blocked
        allowed, count, remaining = limiter.check_rate_limit(
            identifier="test_user",
            endpoint="test_endpoint",
            max_requests=5,
            window=60
        )
        assert allowed is False
        assert count >= 5
        assert remaining == 0
    
    def test_rate_limit_different_identifiers(self):
        """Test that rate limiting is per identifier"""
        limiter = RateLimiter()
        
        # User 1 makes requests
        for i in range(5):
            allowed, _, _ = limiter.check_rate_limit(
                identifier="user1",
                endpoint="test_endpoint",
                max_requests=5,
                window=60
            )
            assert allowed is True
        
        # User 2 should still be able to make requests
        allowed, count, remaining = limiter.check_rate_limit(
            identifier="user2",
            endpoint="test_endpoint",
            max_requests=5,
            window=60
        )
        assert allowed is True
        assert count == 1
        assert remaining == 4
    
    def test_rate_limit_different_endpoints(self):
        """Test that rate limiting is per endpoint"""
        limiter = RateLimiter()
        
        # Make requests to endpoint 1
        for i in range(5):
            allowed, _, _ = limiter.check_rate_limit(
                identifier="test_user",
                endpoint="endpoint1",
                max_requests=5,
                window=60
            )
            assert allowed is True
        
        # Endpoint 2 should have separate limit
        allowed, count, remaining = limiter.check_rate_limit(
            identifier="test_user",
            endpoint="endpoint2",
            max_requests=5,
            window=60
        )
        assert allowed is True
        assert count == 1
        assert remaining == 4
    
    def test_rate_limit_window_expiry(self):
        """Test that rate limit window expires correctly"""
        limiter = RateLimiter()
        
        # Make requests up to limit
        for i in range(5):
            allowed, _, _ = limiter.check_rate_limit(
                identifier="test_user",
                endpoint="test_endpoint",
                max_requests=5,
                window=1  # 1 second window for testing
            )
            assert allowed is True
        
        # Should be blocked
        allowed, _, _ = limiter.check_rate_limit(
            identifier="test_user",
            endpoint="test_endpoint",
            max_requests=5,
            window=1
        )
        assert allowed is False
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, count, remaining = limiter.check_rate_limit(
            identifier="test_user",
            endpoint="test_endpoint",
            max_requests=5,
            window=1
        )
        assert allowed is True
        assert count == 1
        assert remaining == 4
    
    def test_rate_limit_key_generation(self):
        """Test rate limit key generation"""
        limiter = RateLimiter()
        
        key1 = limiter._get_key("user1", "endpoint1")
        key2 = limiter._get_key("user2", "endpoint1")
        key3 = limiter._get_key("user1", "endpoint2")
        
        assert key1 != key2  # Different users
        assert key1 != key3  # Different endpoints
        assert key2 != key3
    
    def test_rate_limit_remaining_calculation(self):
        """Test remaining requests calculation"""
        limiter = RateLimiter()
        
        max_requests = 10
        
        for i in range(3):
            allowed, count, remaining = limiter.check_rate_limit(
                identifier="test_user",
                endpoint="test_endpoint",
                max_requests=max_requests,
                window=60
            )
            assert remaining == max_requests - count
            assert remaining >= 0

