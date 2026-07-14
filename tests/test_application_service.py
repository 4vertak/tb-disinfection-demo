"""Tests for application service."""
import pytest
from app.domain.models.application.entities import Application, Doctor, Area, Diagnosis, EpidemicFocus, Disinfection
from app.domain.models.user.entities import User
from datetime import datetime, date


class TestApplicationModel:
    """Tests for Application model."""

    def test_application_creation(self, db_session, test_user, area, diagnosis, focus):
        """Test creating a basic application with required fields."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Иванов Иван Иванович',
            birth_date=date(1990, 1, 15),
            address='г. Якутск, ул. Ленина, д. 1',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(application)
        db_session.commit()

        assert application.id is not None
        assert application.user_id == test_user.id
        assert application.patient_full_name == 'Иванов Иван Иванович'
        assert application.status == 'incompleted'
        assert len(application.disinfection) >= 1

    def test_application_with_disinfection(self, db_session, test_user, area, diagnosis, focus):
        """Test that Application creates Disinfection on init."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Петров Пётр Петрович',
            birth_date=date(1985, 5, 20),
            address='г. Якутск, пр. Ленина, д. 10',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(application)
        db_session.commit()

        assert len(application.disinfection) == 1
        assert application.disinfection[0].application_id == application.id


class TestApplicationCRUD:
    """Tests for Application CRUD operations."""

    def test_create_application_with_details(self, db_session, test_user, area, diagnosis, focus):
        """Test creating application with all details."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Сидоров Сидор Сидорович',
            birth_date=date(1978, 3, 10),
            address='г. Якутск, ул. Пушкина, д. 5',
            contact_phone='+79141234567',
            relative_contact_phone='+79147654321',
            workplace='ООО "Пример"',
            position='Инженер',
            diagnosis_id=diagnosis.id,
            gdu='123',
            focus_id=focus.id,
            area_id=area.id,
            reason_application='hospitalization'
        )
        db_session.add(application)
        db_session.commit()

        retrieved = db_session.query(Application).filter_by(id=application.id).first()
        assert retrieved.patient_full_name == 'Сидоров Сидор Сидорович'
        assert retrieved.contact_phone == '+79141234567'
        assert retrieved.workplace == 'ООО "Пример"'

    def test_update_application_status(self, db_session, test_user, area, diagnosis, focus):
        """Test updating application status."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Тестовый Пациент',
            birth_date=date(1995, 7, 25),
            address='г. Якутск, ул. Тестовая, д. 1',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id,
            status='incompleted'
        )
        db_session.add(application)
        db_session.commit()

        application.status = 'completed'
        db_session.commit()

        updated = db_session.query(Application).filter_by(id=application.id).first()
        assert updated.status == 'completed'

    def test_delete_application(self, db_session, test_user, area, diagnosis, focus):
        """Test deleting application."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Удаляемый Пациент',
            birth_date=date(2000, 1, 1),
            address='г. Якутск, ул. Удаляемая, д. 1',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(application)
        db_session.commit()
        app_id = application.id

        db_session.delete(application)
        db_session.commit()

        deleted = db_session.query(Application).filter_by(id=app_id).first()
        assert deleted is None

    def test_filter_applications_by_status(self, db_session, test_user, area, diagnosis, focus):
        """Test filtering applications by status."""
        statuses = ['incompleted', 'completed', 'refusal']
        for i, status in enumerate(statuses):
            app = Application(
                user_id=test_user.id,
                submission_date=datetime.now(),
                patient_full_name=f'Пациент {i}',
                birth_date=date(1990, 1, 1),
                address=f'Адрес {i}',
                diagnosis_id=diagnosis.id,
                focus_id=focus.id,
                area_id=area.id,
                status=status
            )
            db_session.add(app)
        db_session.commit()

        completed = db_session.query(Application).filter_by(status='completed').all()
        assert len(completed) == 1
        assert completed[0].status == 'completed'

        incompleted = db_session.query(Application).filter_by(status='incompleted').all()
        assert len(incompleted) == 1


class TestApplicationRelationships:
    """Tests for Application relationships."""

    def test_application_doctor_relationship(self, db_session, test_user, area, diagnosis, focus):
        """Test linking application to doctor."""
        doctor = Doctor(
            full_name='Dr. Test',
            area_id=area.id
        )
        db_session.add(doctor)
        db_session.commit()

        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент с Доктором',
            birth_date=date(1988, 8, 8),
            address='г. Якутск, ул. Доктора, д. 1',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id,
            doctor_id=doctor.id
        )
        db_session.add(application)
        db_session.commit()

        retrieved = db_session.query(Application).filter_by(id=application.id).first()
        assert retrieved.doctor is not None
        assert retrieved.doctor.full_name == 'Dr. Test'

    def test_application_area_relationship(self, db_session, test_user, area, diagnosis, focus):
        """Test linking application to area."""
        application = Application(
            user_id=test_user.id,
            submission_date=datetime.now(),
            patient_full_name='Пациент с Участком',
            birth_date=date(1992, 12, 12),
            address='г. Якутск, ул. Участковая, д. 1',
            diagnosis_id=diagnosis.id,
            focus_id=focus.id,
            area_id=area.id
        )
        db_session.add(application)
        db_session.commit()

        retrieved = db_session.query(Application).filter_by(id=application.id).first()
        assert retrieved.area is not None
        assert retrieved.area.name_area == area.name_area


class TestApplicationQueries:
    """Tests for Application queries."""

    def test_count_applications_by_user(self, db_session, test_user, area, diagnosis, focus):
        """Test counting applications per user."""
        for i in range(3):
            app = Application(
                user_id=test_user.id,
                submission_date=datetime.now(),
                patient_full_name=f'Пациент {i}',
                birth_date=date(1990, 1, 1),
                address=f'Адрес {i}',
                diagnosis_id=diagnosis.id,
                focus_id=focus.id,
                area_id=area.id
            )
            db_session.add(app)
        db_session.commit()

        count = db_session.query(Application).filter_by(user_id=test_user.id).count()
        assert count == 3

    def test_order_applications_by_date(self, db_session, test_user, area, diagnosis, focus):
        """Test ordering applications by submission date."""
        dates = [
            datetime(2024, 1, 1),
            datetime(2024, 1, 15),
            datetime(2024, 2, 1)
        ]
        for i, dt in enumerate(dates):
            app = Application(
                user_id=test_user.id,
                submission_date=dt,
                patient_full_name=f'Пациент {i}',
                birth_date=date(1990, 1, 1),
                address=f'Адрес {i}',
                diagnosis_id=diagnosis.id,
                focus_id=focus.id,
                area_id=area.id
            )
            db_session.add(app)
        db_session.commit()

        ordered = db_session.query(Application).order_by(Application.submission_date.desc()).all()
        assert ordered[0].submission_date == datetime(2024, 2, 1)
        assert ordered[-1].submission_date == datetime(2024, 1, 1)

    @pytest.mark.parametrize('status,expected_count', [
        ('incompleted', 1),
        ('completed', 2),
        ('refusal', 1),
    ])
    def test_application_status_distribution(self, db_session, test_user, area, diagnosis, focus, status, expected_count):
        """Test application count by status."""
        status_distribution = ['incompleted', 'completed', 'completed', 'refusal']
        for i, s in enumerate(status_distribution):
            app = Application(
                user_id=test_user.id,
                submission_date=datetime.now(),
                patient_full_name=f'Пациент {i}',
                birth_date=date(1990, 1, 1),
                address=f'Адрес {i}',
                diagnosis_id=diagnosis.id,
                focus_id=focus.id,
                area_id=area.id,
                status=s
            )
            db_session.add(app)
        db_session.commit()

        count = db_session.query(Application).filter_by(status=status).count()
        assert count == expected_count
