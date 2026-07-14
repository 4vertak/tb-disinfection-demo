from datetime import datetime, timezone
from sqlalchemy import func
from ...core.extensions import db
from ...utils.date_utils import to_local
from ..models.application.entities import ApplicationCounter, Application


class ApplicationNumberService:
    
    @staticmethod
    def initialize_existing_applications(specific_year=None):
        """Присвоить номера существующим заявкам"""
        from ...utils.date_utils import to_local
        
        # Получаем все заявки без номеров, отсортированные по дате создания
        query = Application.query.filter(Application.application_number.is_(None))
        
        if specific_year:
            # Если указан конкретный год, фильтруем по нему
            query = query.filter(
                Application.submission_date >= f"{specific_year}-01-01",
                Application.submission_date < f"{specific_year + 1}-01-01"
            )
        
        applications = query.order_by(Application.submission_date).all()
        
        if not applications:
            return "Нет заявок для инициализации"
        
        # Группируем заявки по годам (в локальной временной зоне)
        applications_by_year = {}
        for app in applications:
            if app.submission_date:
                year = to_local(app.submission_date).year
                if year not in applications_by_year:
                    applications_by_year[year] = []
                applications_by_year[year].append(app)
        
        total_initialized = 0
        
        # Для каждого года присваиваем порядковые номера
        for year, year_applications in applications_by_year.items():
            if specific_year and year != specific_year:
                continue
                
            # Получаем или создаем счетчик для года
            counter = ApplicationCounter.query.filter_by(year=year).first()
            if not counter:
                counter = ApplicationCounter(year=year, last_number=0)
                db.session.add(counter)
            
            # Начинаем нумерацию с последнего номера + 1 или с 1
            start_number = counter.last_number + 1 if counter.last_number > 0 else 1
            
            # Присваиваем номера в хронологическом порядке
            for index, app in enumerate(year_applications, start_number):
                app.application_number = index
            
            # Обновляем счетчик до максимального номера
            new_max_number = max(counter.last_number, start_number + len(year_applications) - 1)
            counter.last_number = new_max_number
            
            total_initialized += len(year_applications)
        
        db.session.commit()
        return f"Инициализировано номеров для {total_initialized} существующих заявок"

    @staticmethod
    def get_next_application_number():
        """Получить следующий порядковый номер заявки для текущего года"""
        current_year = to_local(datetime.now(timezone.utc)).year
        
        # Блокируем запись для текущего года чтобы избежать гонки
        counter = ApplicationCounter.query.filter_by(year=current_year).with_for_update().first()
        
        if not counter:
            # Создаем новую запись для текущего года
            counter = ApplicationCounter(year=current_year, last_number=0)
            db.session.add(counter)
        
        counter.last_number += 1
        next_number = counter.last_number
        
        db.session.flush()
        
        return next_number

    @staticmethod
    def get_application_year(application_date):
        """Получить год заявки в локальной временной зоне"""
        return to_local(application_date).year