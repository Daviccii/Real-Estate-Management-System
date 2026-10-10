"""
Security tests for admin endpoints.
Verify that admin endpoints are properly protected with role-based authorization.
"""
import pytest
import random
from fastapi.testclient import TestClient

from app.main import app

def test_admin_dashboard_requires_admin_role(client):
    """Test that admin dashboard returns 403 for non-admin users."""
    # Create a regular user
    unique_email = f"user_{random.randint(1000, 9999)}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code in (200, 201)
    
    # Login as regular user
    resp = client.post('/api/auth/login', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access
    
    # Try to access admin dashboard as regular user
    headers = {"Authorization": f"Bearer {access}"}
    resp = client.get('/api/admin/dashboard', headers=headers)
    assert resp.status_code == 403  # Forbidden


def test_admin_dashboard_requires_authentication(client):
    """Test that admin dashboard returns 401 for unauthenticated requests."""
    resp = client.get('/api/admin/dashboard')
    assert resp.status_code == 401  # Unauthorized


def test_admin_users_requires_admin_role(client):
    """Test that admin users endpoint returns 403 for non-admin users."""
    unique_email = f"user_{random.randint(1000, 9999)}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code in (200, 201)
    
    resp = client.post('/api/auth/login', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access
    
    headers = {"Authorization": f"Bearer {access}"}
    resp = client.get('/api/admin/users', headers=headers)
    assert resp.status_code == 403  # Forbidden


def test_admin_properties_requires_admin_role(client):
    """Test that admin properties endpoint returns 403 for non-admin users."""
    unique_email = f"user_{random.randint(1000, 9999)}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code in (200, 201)
    
    resp = client.post('/api/auth/login', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access
    
    headers = {"Authorization": f"Bearer {access}"}
    resp = client.get('/api/admin/properties', headers=headers)
    assert resp.status_code == 403  # Forbidden


def test_admin_market_insights_requires_admin_role(client):
    """Test that admin market insights endpoint returns 403 for non-admin users."""
    unique_email = f"user_{random.randint(1000, 9999)}@example.com"
    resp = client.post('/api/auth/register', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code in (200, 201)
    
    resp = client.post('/api/auth/login', json={"email": unique_email, "password": "Str0ng!TestPass42"})
    assert resp.status_code == 200
    access = resp.json().get('access_token')
    assert access
    
    headers = {"Authorization": f"Bearer {access}"}
    resp = client.get('/api/admin/market-insights', headers=headers)
    assert resp.status_code == 403  # Forbidden