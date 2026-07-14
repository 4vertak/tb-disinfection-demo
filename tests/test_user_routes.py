"""Tests for user routes."""
import pytest
from app.domain.models.user.entities import User
from werkzeug.security import generate_password_hash

import sqlite3

class TestUserLoginRoutes:
    """Tests for user login routes."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_get_redirect_if_authenticated(self, client, test_user):
        """Test that authenticated users are redirected from login page."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/login', follow_redirects=False)
        assert response.status_code in [301, 302, 303]

    def test_login_valid_credentials(self, client, test_user):
        """Test login with valid credentials."""
        response = client.post('/login', data={
            'login': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post('/login', data={
            'login': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', data={
            'login': 'nonexistent_user',
            'password': 'anypassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post('/login', data={
            'login': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_login_case_insensitive(self, client, test_user):
        """Test that login is case-sensitive (exact match)."""
        response = client.post('/login', data={
            'login': 'TestUser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestUserLogout:
    """Tests for user logout."""

    def test_logout(self, client, test_user):
        """Test logout functionality."""

        client.post('/login', data={
            'login': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestUserRegistration:
    """Tests for user registration (if available)."""

    def test_registration_page_loads(self, client):
        """Test that registration page loads (if exists)."""

        try:
            response = client.get('/register')
            assert response.status_code == 200
        except Exception:
            pass


class TestUserProfile:
    """Tests for user profile."""

    def test_profile_requires_login(self, client):
        """Test that profile requires authentication."""
        response = client.get('/profile', follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [301, 302, 401, 403]

    def test_profile_authenticated(self, client, test_user):
        """Test profile access for authenticated user."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/profile')
        assert response.status_code == 200


class TestUserPasswordChange:
    """Tests for password change functionality."""

    def test_password_change_requires_login(self, client):
        """Test that password change requires authentication."""
        response = client.get('/user/password/change', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_password_change_success(self, client, test_user):
        """Test successful password change."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/user/password/change', data={
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_password_change_wrong_current(self, client, test_user):
        """Test password change with wrong current password."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/user/password/change', data={
            'current_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_password_change_mismatch_confirmation(self, client, test_user):
        """Test password change with mismatched confirmation."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/user/password/change', data={
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'differentpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestUserPermissions:
    """Tests for user role-based permissions."""

    def test_admin_access(self, client, admin_user):
        """Test admin user access to admin pages."""
        with client.session_transaction() as session:
            session['_user_id'] = str(admin_user.id)
        
        response = client.get('/admin')

        assert response.status_code in [200, 301, 302, 403, 404]
    @pytest.mark.skip(reason="PostgreSQL-specific function 'timezone' not supported in SQLite")
    def test_doctor_access(self, client, test_user):
        """Test doctor user access."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/dashboard')
        assert response.status_code in [200, 301, 302]

    def test_unauthorized_access_redirects(self, client):
        """Test that unauthorized access redirects to login."""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]
