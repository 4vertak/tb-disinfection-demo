import logging
import os
import secrets
import string
from datetime import datetime
from ..models.user.entities import User

from ..models.application.entities import Area, Diagnosis, Disinfector, EpidemicFocus, Doctor
from ...core.extensions import db
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)


class UserInitializer:
    """Сервис для инициализации пользователей и справочников"""

    @staticmethod
    def _generate_secure_password(length: int = 16) -> str:
        """Генерирует случайный пароль заданной длины"""
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def create_admin_account():
        """
        Создает учетную запись администратора по умолчанию,
        если она не существует (только при первом запуске).
        Пароль берётся из переменной окружения ADMIN_PASSWORD.
        Если переменная не задана — генерируется случайный 16-символьный пароль,
        который выводится в лог.
        """
        # НЕ создавать админа, если он уже существует
        admin_exists = User.query.filter_by(user_type='admin').first()
        if admin_exists:
            return False

        # Определяем пароль
        admin_password = os.environ.get('ADMIN_PASSWORD', None)
        if not admin_password:
            admin_password = UserInitializer._generate_secure_password()
            logger.warning(
                "Переменная окружения ADMIN_PASSWORD не задана. "
                "Сгенерирован случайный пароль администратора: %s",
                admin_password
            )
        else:
            logger.info("Создаётся учётная запись администратора из переменной окружения ADMIN_PASSWORD.")

        try:
            admin = User(
                login='admin',
                name='admin',
                password_hash=generate_password_hash(admin_password),
                user_type='admin'
            )
            db.session.add(admin)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create admin account: {str(e)}")

    @staticmethod
    def fill_directories():
        """
        Заполняет системные справочники начальными данными:
        - Участки
        - Эпидемические группы
        - Диагнозы
        """
        try:
            # 1. Заполнение участков
            areas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "ДПДО", "РПТД"]
            for area_name in areas:
                if not Area.query.filter_by(name_area=area_name).first():
                    db.session.add(Area(name_area=area_name))

            # 2. Заполнение эпидемических групп
            epidemic_groups = ["I", "II", "III", "IV", "V", "безадресные"]
            for group_name in epidemic_groups:
                if not EpidemicFocus.query.filter_by(name=group_name).first():
                    db.session.add(EpidemicFocus(name=group_name))

            # 3. Заполнение диагнозов
            diagnoses_data = [
                {"mkb_code": "A15", "name": "A15 - Туберкулез органов дыхания, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.0", "name": "A15.0 - Туберкулез легких, подтвержденный бактериоскопически с наличием или отсутствием роста культуры"},
                {"mkb_code": "A15.1", "name": "A15.1 - Туберкулез легких, подтвержденный только ростом культуры"},
                {"mkb_code": "A15.2", "name": "A15.2 - Туберкулез легких, подтвержденный гистологически"},
                {"mkb_code": "A15.3", "name": "A15.3 - Туберкулез легких, подтвержденный неуточненными методами"},
                {"mkb_code": "A15.4", "name": "A15.4 - Туберкулез внутригрудных лимфатических узлов, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.5", "name": "A15.5 - Туберкулез гортани, трахеи и бронхов, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.6", "name": "A15.6 - Туберкулезный плеврит, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.7", "name": "A15.7 - Первичный туберкулез органов дыхания, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.8", "name": "A15.8 - Туберкулез других органов дыхания, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A15.9", "name": "A15.9 - Туберкулез органов дыхания неуточненной локализации, подтвержденный бактериологически и гистологически"},
                {"mkb_code": "A16", "name": "A16 - Туберкулез органов дыхания, не подтвержденный бактериологически или гистологически"},
                {"mkb_code": "A16.0", "name": "A16.0 - Туберкулез легких при отрицательных результатах бактериологических и гистологических исследований"},
                {"mkb_code": "A16.1", "name": "A16.1 - Туберкулез легких без проведения бактериологического и гистологического исследований"},
                {"mkb_code": "A16.2", "name": "A16.2 - Туберкулез легких без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.3", "name": "A16.3 - Туберкулез внутригрудных лимфатических узлов без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.4", "name": "A16.4 - Туберкулез гортани, трахеи и бронхов без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.5", "name": "A16.5 - Туберкулезный плеврит без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.7", "name": "A16.7 - Первичный туберкулез органов дыхания без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.8", "name": "A16.8 - Туберкулез других органов дыхания без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A16.9", "name": "A16.9 - Туберкулез органов дыхания неуточненной локализации без упоминания о бактериологическом или гистологическом подтверждении"},
                {"mkb_code": "A17", "name": "A17 - Туберкулез нервной системы"},
                {"mkb_code": "A17.0", "name": "A17.0 - Туберкулезный менингит (G01*)"},
                {"mkb_code": "A17.1", "name": "A17.1 - Менингеальная туберкулема (G07*)"},
                {"mkb_code": "A17.8", "name": "A17.8 - Туберкулез нервной системы других локализаций"},
                {"mkb_code": "A17.9", "name": "A17.9 - Туберкулез нервной системы неуточненный (G99.8*)"},
                {"mkb_code": "A18", "name": "A18 - Туберкулез других органов"},
                {"mkb_code": "A18.0", "name": "A18.0 - Туберкулез костей и суставов"},
                {"mkb_code": "A18.1", "name": "A18.1 - Туберкулез мочеполовых органов"},
                {"mkb_code": "A18.2", "name": "A18.2 - Туберкулезная периферическая лимфаденопатия"},
                {"mkb_code": "A18.3", "name": "A18.3 - Туберкулез кишечника, брюшины и брыжеечных лимфатических узлов"},
                {"mkb_code": "A18.4", "name": "A18.4 - Туберкулез кожи и подкожной клетчатки"},
                {"mkb_code": "A18.5", "name": "A18.5 - Туберкулез глаза"},
                {"mkb_code": "A18.6", "name": "A18.6 - Туберкулез уха"},
                {"mkb_code": "A18.7", "name": "A18.7 - Туберкулез надпочечников (E35.1*)"},
                {"mkb_code": "A18.8", "name": "A18.8 - Туберкулез других уточненных органов"},
                {"mkb_code": "A19", "name": "A19 - Милиарный туберкулез"},
                {"mkb_code": "A19.0", "name": "A19.0 - Острый милиарный туберкулез одной уточненной локализации"},
                {"mkb_code": "A19.1", "name": "A19.1 - Острый милиарный туберкулез множественной локализации"},
                {"mkb_code": "A19.2", "name": "A19.2 - Острый милиарный туберкулез неуточненной локализации"},
                {"mkb_code": "A19.8", "name": "A19.8 - Другие формы милиарного туберкулеза"},
                {"mkb_code": "A19.9", "name": "A19.9 - Милиарный туберкулез неуточненной локализации"},
                {"mkb_code": "Z03", "name": "Z03 - Медицинское наблюдение и оценка при подозрении на заболевание или патологическое состояние"},
                {"mkb_code": "Z20.1", "name": "Z20.1 - Контакт с больным и возможность заражения туберкулезом"},
                {"mkb_code": "Y58.0", "name": "Y58.0 - Осложнения от введения вакцины БЦЖ"},
                {"mkb_code": "R76.1", "name": "R76.1 - Аномальная реакция на туберкулиновую пробу"},
                {"mkb_code": "B90", "name": "B90 - Отдаленные последствия туберкулеза"}
            ]
            for diagnosis in diagnoses_data:
                if not Diagnosis.query.filter_by(mkb_code=diagnosis["mkb_code"]).first():
                    db.session.add(Diagnosis(**diagnosis))

            # 4. Заполнение справочника дезинфекторов
            disinfectors = ["Антонов А.А.", "Борисова Б.Б.", "Васильев В.В.", "Григорьева Г.Г.", "Дмитриев Д.Д."]
            for disinfector_name in disinfectors:
                if not Disinfector.query.filter_by(full_name=disinfector_name).first():
                    db.session.add(Disinfector(full_name=disinfector_name))

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to fill directories: {str(e)}")


class UserService:
    """Сервис для работы с пользователями"""

    @staticmethod
    def create_user(user_data):
        """
        Создает нового пользователя
        Args:
            user_data (dict): {
                "login": str,
                "name": str,
                "password": str,
                "user_type": str (admin, doctor, disinfector и т.п.),
                "area_id": int (optional, для врачей)
            }
        Returns:
            User
        """
        try:
            user = User(
                login =user_data['login'],
                name =user_data['name'],
                password_hash=generate_password_hash(user_data['password']),
                user_type=user_data['user_type']
            )
            # Сохраняем участок если это врач
            if user_data.get('area_id'):
                user.area_id = user_data['area_id']
            
            db.session.add(user)
            db.session.commit()
            return user

        except Exception as e:
            db.session.rollback()
            raise Exception(f"User creation failed: {str(e)}")

    @staticmethod
    def get_user_by_id(user_id):
        """Возвращает пользователя по ID"""
        return db.session.get(User, user_id)

    @staticmethod
    def update_user(user_id, update_data):
        """
        Обновляет данные пользователя
        Args:
            user_id (int)
            update_data (dict)
        """
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        try:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            db.session.commit()
            return user

        except Exception as e:
            db.session.rollback()
            raise Exception(f"User update failed: {str(e)}")
