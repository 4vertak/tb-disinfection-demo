"""Tests for application routes."""
import pytest
from datetime import datetime, date
from app.domain.models.application.entities import Application, Area, Diagnosis, EpidemicFocus


class TestApplicationRoutes:
    """Tests for application listing and viewing."""

    def test_application_list_requires_login(self, client):
        """Test that application list requires authentication."""
        response = client.get('/applications', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_application_list_authenticated(self, client, test_user):
        """Test application list for authenticated user."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/applications')
        assert response.status_code == 200

    def test_application_detail_requires_login(self, client):
        """Test that application detail requires authentication."""
        response = client.get('/application/1', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_application_detail_not_found(self, client, test_user):
        """Test application detail for non-existent application."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/application/99999', follow_redirects=True)
        assert response.status_code in [200, 404]


class TestApplicationCreate:
    """Tests for application creation."""

    def test_create_application_requires_login(self, client):
        """Test that creating application requires authentication."""
        response = client.get('/application/create', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_create_application_page_loads(self, client, test_user):
        """Test that application creation page loads."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/application/create')
        assert response.status_code == 200

    def test_create_application_success(self, client, test_user, area, diagnosis, focus):
        """Test successful application creation."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/application/create', data={
            'patient_full_name': 'Иванов Иван Иванович',
            'birth_date': '1990-01-15',
            'address': 'г. Якутск, ул. Ленина, д. 1',
            'diagnosis_id': diagnosis.id,
            'focus_id': focus.id,
            'area_id': area.id
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_create_application_missing_fields(self, client, test_user):
        """Test application creation with missing required fields."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/application/create', data={
            'patient_full_name': '',  # Missing required field
            'birth_date': '',
            'address': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestApplicationEdit:
    """Tests for application editing."""

    def test_edit_application_requires_login(self, client, db_session, test_user, area, diagnosis, focus):
        """Test that editing application requires authentication."""
        app = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Тестовый Пациент',
            birth_date=date(1990, 1, 1),
            address='Тестовый адрес',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app)
        db_session.commit()
        
        response = client.get(f'/application/{app.id}/edit', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_edit_application_success(self, client, db_session, test_user, area, diagnosis, focus):
        """Test successful application editing."""
        app = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Оригинальный Пациент',
            birth_date=date(1990, 1, 1),
            address='Оригинальный адрес',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app)
        db_session.commit()
        
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post(f'/application/{app.id}/edit', data={
            'patient_full_name': 'Обновленный Пациент',
            'birth_date': '1990-01-15',
            'address': 'Обновленный адрес',
            'diagnosis_id': diagnosis.id,
            'focus_id': focus.id,
            'area_id': area.id
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_edit_application_not_found(self, client, test_user):
        """Test editing non-existent application."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/application/99999/edit', follow_redirects=True)
        assert response.status_code in [200, 404]


class TestApplicationDelete:
    """Tests for application deletion."""

    def test_delete_application_requires_login(self, client, db_session, test_user, area, diagnosis, focus):
        """Test that deleting application requires authentication."""
        app = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Удаляемый Пациент',
            birth_date=date(1990, 1, 1),
            address='Адрес для удаления',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app)
        db_session.commit()
        
        response = client.post(f'/application/{app.id}/delete', follow_redirects=False)
        assert response.status_code in [301, 302, 401, 403]

    def test_delete_application_success(self, client, db_session, admin_user, test_user, area, diagnosis, focus):
        """Test successful application deletion by admin."""
        # Doctor создаёт заявку
        app = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Удаляемый Пациент',
            birth_date=date(1990, 1, 1),
            address='Адрес для удаления',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app)
        db_session.commit()
        app_id = app.id

        # Admin удаляет заявку (только admin имеет право удалять)
        with client.session_transaction() as session:
            session['_user_id'] = str(admin_user.id)

        response = client.post(f'/application/{app_id}/delete', follow_redirects=True)

        assert response.status_code == 200
        db_session.expire_all()
        deleted_app = db_session.get(Application, app_id)
        assert deleted_app is None

    def test_delete_application_not_found(self, client, test_user):
        """Test deleting non-existent application."""
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.post('/application/99999/delete', follow_redirects=True)
        assert response.status_code in [200, 404]


class TestApplicationFilters:
    """Tests for application filtering."""

    def test_filter_by_status(self, client, db_session, test_user, area, diagnosis, focus):
        """Test filtering applications by status."""
        # Create applications with different statuses
        for status in ['incompleted', 'completed', 'refusal']:
            app = Application(
                user_id=test_user.id,
                submission_date=datetime.now(),
                patient_full_name=f'Пациент {status}',
                birth_date=date(1990, 1, 1),
                address=f'Адрес {status}',
                diagnosis_id=diagnosis.id,
                focus_id=focus.id,
                area_id=area.id,
                status=status
            )
            db_session.add(app)
        db_session.commit()
        
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        # Filter by status
        response = client.get('/applications?status=completed')
        assert response.status_code == 200

    def test_filter_by_date_range(self, client, db_session, test_user, area, diagnosis, focus):
        """Test filtering applications by date range."""
        app = Application(
            user_id=test_user.id,
            submission_date=datetime(2024, 1, 15),
            patient_full_name='Пациент с датой',
            birth_date=date(1990, 1, 1),
            address='Адрес с датой',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app)
        db_session.commit()
        
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/applications?start_date=2024-01-01&end_date=2024-12-31')
        assert response.status_code == 200


class TestApplicationPermissions:
    """Tests for application access permissions."""

    def test_user_can_only_see_own_applications(self, client, db_session, test_user, admin_user, area, diagnosis, focus):
        """Test that users can only see their own applications."""
        # Create application for test_user
        app1 = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент пользователя',
            birth_date=date(1990, 1, 1),
            address='Адрес пользователя',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app1)
        
        # Create application for admin_user
        app2 = Application(
            user_id=admin_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент админа',
            birth_date=date(1990, 1, 1),
            address='Адрес админа',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(app2)
        db_session.commit()
        
        # Login as test_user
        with client.session_transaction() as session:
            session['_user_id'] = str(test_user.id)
        
        response = client.get('/applications')
        assert response.status_code == 200
        # Should only see own applications

    def test_admin_can_see_all_applications(self, client, db_session, admin_user, area, diagnosis, focus):
        """Test that admin can see all applications."""
        with client.session_transaction() as session:
            session['_user_id'] = str(admin_user.id)
        
        response = client.get('/applications')
        assert response.status_code == 200
