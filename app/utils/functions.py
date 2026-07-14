
from datetime import date, datetime, time
from ..utils.date_utils import to_utc
from docx.shared import Pt
import os.path
import secrets
from PIL import Image

from flask import current_app
from sqlalchemy.orm import aliased
from sqlalchemy import func

from collections import OrderedDict

from ..domain.models.user.entities import User
from ..domain.models.application.entities import Application, Disinfector, Disinfection, EpidemicFocus, Doctor, Area, disinfection_disinfector
from ..core.extensions import db


def save_picture(picture):
    """Сохранение изображения профиля"""
    if picture:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(
            current_app.config['SERVER_PATH'], picture_fn)
        output_size = (125, 125)
        i = Image.open(picture)
        i.thumbnail(output_size)
        i.save(picture_path)
    else:
        picture_fn = 'user.svg'
        picture_path = os.path.join(
            current_app.config['SERVER_PATH'], picture_fn)
    return picture_fn


def recursive_flatten_iterator(d):
    """ Итератор для рекурсивного обхода словаря"""
    for k, v in d.items():
        if isinstance(v, list):
            yield v
        if isinstance(v, dict):
            yield from recursive_flatten_iterator(v)


def set_font_for_document(doc, font_name='Times New Roman', font_size=12):
    """Установка шрифта для документа"""
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = font_name
            run.font.size = Pt(12)




def get_month_list(start_date, end_date):
    """Генерация списка месяцев только с названиями месяцев"""
    months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь",
                "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    
    months = OrderedDict()
    current = start_date.replace(day=1)
    
    while current <= end_date:
        month_key = months_ru[current.month - 1]
        months[month_key] = 0
        
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    return months

def get_monthly_data(model, date_field, start_date, end_date):
    """Получение данных по месяцам (только названия месяцев)"""
    months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь",
                "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    
    monthly_counts = get_month_list(start_date, end_date)
    
    # Преобразуем в UTC для запроса
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    query = (
        db.session.query(
            func.extract('month', func.timezone('Asia/Yakutsk', getattr(model, date_field))).label('month'),
            func.count(model.id).label('count')
        )
        .filter(getattr(model, date_field).between(start_utc, end_utc))
        .group_by('month')
        .order_by('month')
        .all()
    )

    for month_num, count in query:
        month_name = months_ru[int(month_num) - 1]
        if month_name in monthly_counts:
            monthly_counts[month_name] = count

    return monthly_counts

def combine_monthly_data(applicates_data, disinfection_data, start_date, end_date):
    """Объединение данных по месяцам"""
    combined = OrderedDict()
    all_months = get_month_list(start_date, end_date).keys()
    
    for month in all_months:
        combined[month] = {
            'applications': applicates_data.get(month, 0),
            'disinfections': disinfection_data.get(month, 0)
        }
    
    return combined




def get_monthly_data_logs(model, date_field, start_date, end_date):
    """Получение данных по месяцам для логов (только названия месяцев)"""
    months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь",
                "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    
    # Преобразуем в UTC для запроса
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    try:
        monthly_data = db.session.query(
            func.extract('month', func.timezone('Asia/Yakutsk', getattr(model, date_field))).label('month'),
            getattr(model, 'change_type'),
            func.count(getattr(model, 'id')).label('total')
        ).filter(
            getattr(model, date_field).between(start_utc, end_utc)
        ).group_by('month', 'change_type').order_by('month').all()
        
        result = {}
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_str = months_ru[current_date.month - 1]
            result[month_str] = {'INSERT': 0, 'UPDATE': 0, 'DELETE': 0}
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        for entry in monthly_data:
            month_str = months_ru[int(entry.month) - 1]
            if month_str in result and entry.change_type in result[month_str]:
                result[month_str][entry.change_type] = entry.total
                
        return result
    
    except Exception as e:
        # Возвращаем пустые данные для всех месяцев периода
        result = {}
        current_date = start_date.replace(day=1)
        while current_date <= end_date:
            month_str = months_ru[current_date.month - 1]
            result[month_str] = {'INSERT': 0, 'UPDATE': 0, 'DELETE': 0}
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        return result



# def combine_monthly_data(monthly_app_data, monthly_dis_data, start_date, end_date):
#     months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь",
#                  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]

#     combined_data = {}
#     current_date = start_date.replace(day=1)
    
#     while current_date <= end_date:
#         month_str = months_ru[current_date.month - 1]
#         year_str = str(current_date.year)
#         key = f"{month_str} {year_str}"
#         combined_data[key] = {'applications': 0, 'disinfections': 0}
        
#         if current_date.month == 12:
#             current_date = current_date.replace(year=current_date.year + 1, month=1)
#         else:
#             current_date = current_date.replace(month=current_date.month + 1)

#     for date_obj, count in monthly_app_data:
#         month_str = months_ru[date_obj.month - 1]
#         year_str = str(date_obj.year)
#         key = f"{month_str} {year_str}"
#         if key in combined_data:
#             combined_data[key]['applications'] = count

#     for date_obj, count in monthly_dis_data:
#         month_str = months_ru[date_obj.month - 1]
#         year_str = str(date_obj.year)
#         key = f"{month_str} {year_str}"
#         if key in combined_data:
#             combined_data[key]['disinfections'] = count

#     return combined_data



def get_areas_data_applicates(start_date, end_date):
    """Получение данных по участкам для заявок"""
    AppAlias = aliased(Application)
    
    # Преобразуем в UTC для запроса
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    return db.session.query(
        Area.name_area.label('area_name'),
        func.count(AppAlias.id).label('total')
    ).join(AppAlias, AppAlias.area_id == Area.id)\
     .join(Doctor, AppAlias.doctor_id == Doctor.id)\
     .filter(AppAlias.submission_date.between(start_utc, end_utc))\
     .group_by(Area.name_area)\
     .order_by(Area.name_area)\
     .all()

def get_monthly_data_disinfection_completed(start_date, end_date):
    """Получение данных по месяцам для ВЫПОЛНЕННЫХ дезинфекций"""
    months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь",
                "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    
    monthly_counts = get_month_list(start_date, end_date)
    
    # Преобразуем в UTC для запроса
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    query = (
        db.session.query(
            func.extract('month', func.timezone('Asia/Yakutsk', Disinfection.disinfection_date)).label('month'),
            func.count(Disinfection.id).label('count')
        )
        .join(Application, Disinfection.application_id == Application.id)
        .filter(Disinfection.disinfection_date.between(start_utc, end_utc))
        .filter(Application.status == 'completed')  # ФИЛЬТР ПО СТАТУСУ
        .group_by('month')
        .order_by('month')
        .all()
    )

    for month_num, count in query:
        month_name = months_ru[int(month_num) - 1]
        if month_name in monthly_counts:
            monthly_counts[month_name] = count

    return monthly_counts



def get_areas_data_disinfection_completed(start_date, end_date):
    """Получение данных по участкам для ВЫПОЛНЕННЫХ дезинфекций"""
    # Преобразуем в UTC для запроса
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    return db.session.query(
        Area.name_area.label('area_name'),
        func.count(Disinfection.disinfection_date).label('total')
    ).join(Application, Disinfection.application_id == Application.id)\
     .join(Doctor, Application.doctor_id == Doctor.id)\
     .join(Area, Doctor.area_id == Area.id)\
     .filter(Disinfection.disinfection_date.between(start_utc, end_utc))\
     .filter(Application.status == 'completed').group_by(Area.name_area)\
     .order_by(Area.name_area)\
     .all()

def initialize_combined_areas_data():
    """Инициализация комбинированных данных по участкам"""
    return {area.name_area: {'applications': 0, 'disinfections': 0} for area in db.session.query(Area).all()}


def combine_areas_data(areas_data_applicates, areas_data_disinfection):
    """Объединение данных по участкам"""
    combined_areas_data = initialize_combined_areas_data()
    for row in areas_data_applicates:
        combined_areas_data[row.area_name]['applications'] = row.total
    for row in areas_data_disinfection:
        combined_areas_data[row.area_name]['disinfections'] = row.total
    return combined_areas_data


def prepare_areas_labels_and_values(combined_areas_data):
    """Подготовка меток и значений для графика участков"""
    areas_labels = list(combined_areas_data.keys())
    areas_total_values = [data['applications'] for data in combined_areas_data.values()]
    areas_completed_values = [data['disinfections'] for data in combined_areas_data.values()]

    return areas_labels, areas_total_values, areas_completed_values


def get_focus_data(start_date, end_date):
    """Получение данных по эпидемическим группам"""
    # Преобразуем в UTC
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    return db.session.query(
        EpidemicFocus.name.label('focus_name'),
        Area.name_area.label('area_name'),
        func.count(Application.id).label('total')
    ).join(Application, Application.focus_id == EpidemicFocus.id) \
     .join(Disinfection, Disinfection.application_id == Application.id) \
     .join(Doctor, Doctor.id == Application.doctor_id) \
     .join(Area, Area.id == Application.area_id) \
     .filter(Application.submission_date.between(start_utc, end_utc)) \
     .group_by(EpidemicFocus.name, Area.name_area) \
     .order_by(EpidemicFocus.name, Area.name_area).all()
     
def get_focus_data_completed(start_date, end_date):
    """Получение данных по эпидемическим группам для ВЫПОЛНЕННЫХ заявок"""
    # Преобразуем в UTC
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    return db.session.query(
        EpidemicFocus.name.label('focus_name'),
        Area.name_area.label('area_name'),
        func.count(Application.id).label('total')
    ).join(Application, Application.focus_id == EpidemicFocus.id) \
     .join(Disinfection, Disinfection.application_id == Application.id) \
     .join(Doctor, Doctor.id == Application.doctor_id) \
     .join(Area, Area.id == Application.area_id) \
     .filter(Application.submission_date.between(start_utc, end_utc)) \
     .filter(Application.status == 'completed').group_by(EpidemicFocus.name, Area.name_area) \
     .order_by(EpidemicFocus.name, Area.name_area).all()


def initialize_combined_focus_areas_data(focus_data):
    """Инициализация комбинированных данных по эпидемическим группам"""
    combined_focus_areas_data = {}
    for row in focus_data:
        if row.focus_name not in combined_focus_areas_data:
            combined_focus_areas_data[row.focus_name] = {}
        combined_focus_areas_data[row.focus_name][row.area_name] = row.total
    return combined_focus_areas_data


def prepare_labels_and_values(combined_focus_areas_data):
    """Подготовка меток и значений для графика эпидемических групп"""
    focus_labels = list(combined_focus_areas_data.keys())
    area_labels = list(set(
        label for areas in combined_focus_areas_data.values() for label in areas.keys()))
    focus_total_values = {
        focus: [combined_focus_areas_data[focus].get(area, 0) for area in area_labels]
        for focus in focus_labels
    }
    return focus_labels, area_labels, focus_total_values


def prepare_data_for_chart(focus_total_values, focus_labels):
    """Подготовка данных для графика"""
    return [focus_total_values[focus] for focus in focus_labels]

# TODO: Добваить логику определения исполнителей - дезинфекторов.
"""
Логика расчета площади для дезинфекторов:
1. Если по заявке выполнена дезинфекция площадью X м²
2. Если в дезинфекции участвовало N дезинфекторов
3. Тогда каждому дезинфектору засчитывается X/N м²
4. Если дезинфекция без дезинфекторов - площадь не учитывается
5. Если площадь не указана (NULL или 0) - игнорируем запись

Пример:
- Заявка 1: площадь 20 м², 2 дезинфектора → каждый получает 10 м²
- Заявка 2: площадь 30 м², 3 дезинфектора → каждый получает 10 м²
- Итого дезинфектор, участвовавший в обеих заявках: 20 м²
"""
def get_top_disinfectors(start_date, end_date):
    """
    Альтернативный вариант с оконными функциями
    """
    
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)
    
    # Используем оконную функцию для подсчета количества дезинфекторов на дезинфекцию
    disinfectors_per_disinfection = func.count(disinfection_disinfector.c.disinfector_id).over(
        partition_by=disinfection_disinfector.c.disinfection_id
    ).label('disinfectors_per_disinfection')
    
    # Создаем подзапрос с оконной функцией
    subq = db.session.query(
        Disinfection.id,
        Disinfector.full_name,
        Disinfection.area_size,
        disinfectors_per_disinfection
    ).join(
        disinfection_disinfector,
        Disinfection.id == disinfection_disinfector.c.disinfection_id
    ).join(
        Disinfector,
        Disinfector.id == disinfection_disinfector.c.disinfector_id
    ).filter(
        Disinfection.disinfection_date.between(start_utc, end_utc),
        Disinfection.rejection_reason == 'completed',
        Disinfection.area_size > 0
    ).subquery()
    
    # Основной запрос для группировки
    query = db.session.query(
        subq.c.full_name,
        func.count(subq.c.id).label('disinfection_count'),
        func.sum(subq.c.area_size / subq.c.disinfectors_per_disinfection).label('total_area')
    ).group_by(
        subq.c.full_name
    ).order_by(
        func.count(subq.c.id).desc(),
        func.sum(subq.c.area_size / subq.c.disinfectors_per_disinfection).desc()
    ).limit(10)
    
    results = query.all()
    
    return [{
        'id': idx + 1,
        'name': result[0],
        'disinfection_count': result[1],
        'total_area': float(result[2]) if result[2] else 0.0
    } for idx, result in enumerate(results)]