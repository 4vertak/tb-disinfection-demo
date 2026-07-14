"""Marshmallow схемы для dashboard."""
from marshmallow import Schema, fields


class TotalInfoSchema(Schema):
    """Схема для общей статистики"""
    total = fields.Integer(metadata={'description': 'Всего заявок'})
    completed = fields.Integer(metadata={'description': 'Выполнено'})
    in_progress = fields.Integer(metadata={'description': 'В работе'})
    refusal = fields.Integer(metadata={'description': 'Отказы'})
    square_disinfection = fields.Float(metadata={'description': 'Обработанная площадь (м²)'})
    washes = fields.Integer(metadata={'description': 'Взято смывов'})
    count_disinfectors = fields.Integer(metadata={'description': 'Количество дезинфекторов'})
    carry_over = fields.Integer(metadata={'description': 'Переходящие заявки'}, allow_none=True)
    total_with_carry_over = fields.Integer(metadata={'description': 'Всего с переходящими'}, allow_none=True)


class MonthlyDataSchema(Schema):
    """Схема для месячных данных"""
    month = fields.String(metadata={'description': 'Месяц'})
    applications = fields.Integer(metadata={'description': 'Заявок'})
    disinfections = fields.Integer(metadata={'description': 'Выполнено дезинфекций'})


class TopDisinfectorSchema(Schema):
    """Схема для топ дезинфектора"""
    name = fields.String(metadata={'description': 'ФИО дезинфектора'})
    disinfection_count = fields.Integer(metadata={'description': 'Количество дезинфекций'})
    total_area = fields.Float(metadata={'description': 'Общая площадь (м²)'})


class TableRowSchema(Schema):
    """Схема для строки таблицы эпидгрупп"""
    focus = fields.String(metadata={'description': 'Эпидемическая группа'})
    total = fields.Integer(metadata={'description': 'Всего по группе'})
    # Динамические поля для участков (1, 2, 3, ..., ДПДО, РПТД)
    # Используем Raw для гибкости
    data = fields.Raw(metadata={'description': 'Данные по участкам'})


class DashboardSchema(Schema):
    """Полная схема для данных dashboard"""
    period = fields.String(metadata={'description': 'Период'})
    year = fields.Integer(metadata={'description': 'Год'})
    start_date = fields.String(metadata={'description': 'Дата начала'})
    end_date = fields.String(metadata={'description': 'Дата конца'})
    total_info = fields.Nested(TotalInfoSchema, metadata={'description': 'Общая статистика'})
    monthly_data = fields.Raw(metadata={'description': 'Месячные данные'})
    top_disinfectors = fields.List(fields.Nested(TopDisinfectorSchema), metadata={'description': 'Топ дезинфекторов'})
    areas_labels = fields.List(fields.String(), metadata={'description': 'Метки участков'})
    areas_total_values = fields.List(fields.Integer(), metadata={'description': 'Всего по участкам'})
    areas_completed_values = fields.List(fields.Integer(), metadata={'description': 'Выполнено по участкам'})
    chart_data = fields.Raw(metadata={'description': 'Данные для графиков'})
    table_data = fields.List(fields.Raw(), metadata={'description': 'Таблица эпидгрупп'})
    show_square_info = fields.Boolean(metadata={'description': 'Показывать информацию о площади'})
    available_years = fields.List(fields.Integer(), metadata={'description': 'Доступные годы'})