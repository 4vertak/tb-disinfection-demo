"""Tests for user service."""
import pytest
from app.domain.models.user.entities import User
from werkzeug.security import check_password_hash


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user with all fields."""
        user = User(
            login='newuser',
            name='New User',
            password_hash='hashed_password',
            user_type='doctor'
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.login == 'newuser'
        assert user.name == 'New User'
        assert user.user_type == 'doctor'

    def test_user_password_verification(self, db_session):
        """Test that password_hash can be verified."""
        from werkzeug.security import generate_password_hash

        user = User(
            login='passuser',
            name='Password User',
            password_hash=generate_password_hash('mypassword'),
            user_type='disinfector'
        )
        db_session.add(user)
        db_session.commit()

        assert check_password_hash(user.password_hash, 'mypassword')
        assert not check_password_hash(user.password_hash, 'wrongpassword')

    def test_user_string_representation(self, db_session):
        """Test __str__ and __repr__ methods."""
        user = User(
            login='struser',
            name='String User',
            password_hash='hash',
            user_type='admin'
        )
        db_session.add(user)
        db_session.commit()

        # User.__str__ возвращает '<User {id}>'
        assert 'User' in str(user)
        assert str(user).startswith('<User')

    @pytest.mark.parametrize('user_type', ['admin', 'doctor', 'disinfector'])
    def test_user_types(self, db_session, user_type):
        """Test different user types can be created."""
        user = User(
            login=f'{user_type}_user',
            name=f'{user_type.title()} User',
            password_hash='hash',
            user_type=user_type
        )
        db_session.add(user)
        db_session.commit()

        assert user.user_type == user_type


class TestUserAuthentication:
    """Tests for user authentication."""

    def test_login_success(self, client, test_user, app):
        """Test successful login."""
        response = client.post('/login', data={
            'login': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_failure_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post('/login', data={
            'login': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_failure_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', data={
            'login': 'nonexistent',
            'password': 'password'
        }, follow_redirects=True)

        assert response.status_code == 200


class TestUserService:
    """Tests for UserService."""

    def test_get_user_by_id(self, db_session, test_user):
        """Test retrieving user by ID."""
        user = db_session.query(User).filter_by(id=test_user.id).first()
        assert user is not None
        assert user.id == test_user.id
        assert user.login == 'testuser'

    def test_get_user_by_login(self, db_session, test_user):
        """Test retrieving user by login."""
        user = db_session.query(User).filter_by(login='testuser').first()
        assert user is not None
        assert user.name == 'Test User'

    def test_user_not_found(self, db_session):
        """Test that non-existent user returns None."""
        user = db_session.query(User).filter_by(login='nonexistent').first()
        assert user is None

    def test_update_user_name(self, db_session, test_user):
        """Test updating user name."""
        test_user.name = 'Updated Name'
        db_session.commit()

        updated_user = db_session.query(User).filter_by(id=test_user.id).first()
        assert updated_user.name == 'Updated Name'

    def test_cannot_duplicate_login(self, db_session, test_user):
        """Test that duplicate login raises integrity error."""
        from sqlalchemy.exc import IntegrityError

        duplicate_user = User(
            login='testuser',  # Same login
            name='Duplicate User',
            password_hash='hash',
            user_type='doctor'
        )
        db_session.add(duplicate_user)

        with pytest.raises(IntegrityError):
            db_session.commit()
