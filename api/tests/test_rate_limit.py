import pytest
from fastapi import status
import time
import redis

def test_rate_limit_basic(client, mock_redis, mock_ip, mock_services):
    """Test basic rate limiting functionality"""
    # Mock Redis get/set for rate limiting
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    # Make multiple requests
    for _ in range(5):
        response = client.get("/health", headers={"X-Forwarded-For": mock_ip})
        assert response.status_code == status.HTTP_200_OK
    
    # Next request should be rate limited
    response = client.get("/health", headers={"X-Forwarded-For": mock_ip})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

def test_rate_limit_reset(client, mock_redis, mock_ip, mock_services):
    """Test rate limit reset after window expires"""
    # Mock Redis to simulate expired rate limit
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    # First request
    response = client.get("/health", headers={"X-Forwarded-For": mock_ip})
    assert response.status_code == status.HTTP_200_OK
    
    # Mock Redis to simulate expired rate limit
    mock_redis.get.return_value = None
    
    # Should be able to make another request after window expires
    response = client.get("/health", headers={"X-Forwarded-For": mock_ip})
    assert response.status_code == status.HTTP_200_OK

def test_rate_limit_different_ips(client, mock_redis, mock_services):
    """Test rate limiting with different IP addresses"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    # Make requests from different IPs
    for ip in ["192.168.1.1", "192.168.1.2", "192.168.1.3"]:
        response = client.get("/health", headers={"X-Forwarded-For": ip})
        assert response.status_code == status.HTTP_200_OK

def test_rate_limit_no_ip(client, mock_redis, mock_services):
    """Test rate limiting without IP header"""
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    # Request without IP header should still work
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

def test_rate_limit_redis_error(client, mock_redis, mock_ip, mock_services):
    """Test rate limiting when Redis fails"""
    # Mock Redis to raise an exception
    mock_redis.get.side_effect = redis.RedisError("Connection failed")
    
    # Should still allow request when Redis fails
    response = client.get("/health", headers={"X-Forwarded-For": mock_ip})
    assert response.status_code == status.HTTP_200_OK 

def test_health_endpoint(client, mock_services):
    """Test that the health endpoint returns 200 OK"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert "status" in response.json()
    assert response.json()["status"] == "healthy" 