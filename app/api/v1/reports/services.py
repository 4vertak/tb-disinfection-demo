# app/api/v1/reports/services.py
"""Бизнес-логика для отчётов."""
from datetime import datetime, timezone
from io import BytesIO
from app.domain.services.import_export_service import ExcelImportExportService
from app.domain.services.application_service import ApplicationService
from app.utils.date_utils import get_period_dates, to_utc


class ReportsApiService:
    """Сервис для генерации отчётов через API"""
    
    @staticmethod
    def export_applications_excel(period: str = 'year', year: int = None, user=None):
        """Экспорт заявок в Excel"""
        if year is None:
            year = datetime.now(timezone.utc).year
        
        start_date, end_date = get_period_dates(period, year)
        
        # Используем существующий сервис
        user_type = user.user_type if user else None
        excel_data = ExcelImportExportService.export_to_excel(
            start_date, end_date, user_type
        )
        
        return excel_data, f'applications_{year}_{period}.xlsx'
    
    @staticmethod
    def generate_application_document(application_id: int):
        """Генерация Word документа заявки"""
        # Используем существующий сервис
        doc_stream = ApplicationService.generate_application_doc(application_id)
        
        from app.domain.models.application.entities import Application
        from app.core.extensions import db
        from app.utils.date_utils import to_local
        
        application = db.session.get(Application, application_id)
        if not application:
            raise ValueError('Application not found')
        
        current_date = to_local(datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        display_id = application.application_number or application.id
        filename = f"application_{display_id}_{current_date}.docx"
        
        return doc_stream, filename