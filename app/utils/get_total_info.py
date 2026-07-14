from datetime import datetime, time, date
from sqlalchemy import func, case, and_
from app.utils.date_utils import to_utc, LOCAL_TZ
from ..domain.models.application.entities import Application, Disinfection
from ..core.extensions import db

def get_total_info(start_date, end_date):
    """
    Получение общей информации за отчётный период.
    start_date и end_date уже в Asia/Yakutsk.
    Возвращает словарь с показателями:
        total: заявки, созданные в периоде
        completed: завершённые (completed) в периоде (по disinfection_date)
        refusal: отказы (refusal) в периоде (по disinfection_date)
        in_progress: незавершённые заявки на конец периода (status='incompleted' и submission_date <= end_date)
        washes: сумма смывов (swab_testing) за период
        carry_over: переходящие заявки (созданы до start_date и числятся в периоде)
        total_with_carry_over: общее количество заявок, учитываемых в периоде
    """
    if start_date is None or end_date is None:
        return {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'refusal': 0,
            'washes': 0,
            'carry_over': 0,
            'total_with_carry_over': 0
        }

    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    # 1. Заявки, созданные в отчётном периоде
    total_created = Application.query.filter(
        Application.submission_date.between(start_utc, end_utc)
    ).count()

    # 2. Переходящие заявки (созданы до start_date)
    #    - незавершённые (incompleted)
    in_progress_carry = Application.query.filter(
        Application.submission_date < start_utc,
        Application.status == 'incompleted'
    ).count()
    #    - завершённые (completed или refusal) в периоде
    completed_refusal_carry = db.session.query(Application).join(
        Disinfection, Disinfection.application_id == Application.id
    ).filter(
        Application.submission_date < start_utc,
        Application.status.in_(['completed', 'refusal']),
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).distinct().count()

    carry_over = in_progress_carry + completed_refusal_carry

    # 3. Завершённые заявки в периоде (completed)
    completed = db.session.query(Application).join(
        Disinfection, Disinfection.application_id == Application.id
    ).filter(
        Application.status == 'completed',
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).distinct().count()

    # 4. Отказы в периоде (refusal)
    refusal = db.session.query(Application).join(
        Disinfection, Disinfection.application_id == Application.id
    ).filter(
        Application.status == 'refusal',
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).distinct().count()

    # 5. Незавершённые заявки на конец периода
    in_progress = Application.query.filter(
        Application.status == 'incompleted',
        Application.submission_date <= end_utc
    ).count()

    # 6. Сумма смывов
    washes = Disinfection.query.filter(
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).with_entities(db.func.sum(Disinfection.swab_testing)).scalar() or 0

    total_with_carry_over = total_created + carry_over

    return {
        'total': total_created,
        'completed': completed,
        'in_progress': in_progress,
        'refusal': refusal,
        'washes': washes,
        'carry_over': carry_over,
        'total_with_carry_over': total_with_carry_over
    }

def get_carry_over_count(start_date, end_date):
    """
    Подсчёт переходящих заявок за отчётный период.
    
    Переходящими считаются заявки, которые:
    1. Созданы ДО начала отчётного периода (submission_date < start_date).
    2. На момент отчёта находятся в одном из состояний:
       - статус 'incompleted' (ещё не завершены, числятся в работе),
       - статус 'completed' или 'refusal' с датой дезинфекции/отказа,
         попадающей в отчётный период [start_date, end_date].
    
    Параметры:
        start_date (datetime): начало отчётного периода (в локальном времени).
        end_date (datetime): конец отчётного периода (в локальном времени).
    
    Возвращает:
        int: количество переходящих заявок.
    """
    if start_date is None or end_date is None:
        return 0

    # Преобразуем границы периода в UTC (как хранятся в БД)
    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    # 1. Незавершённые заявки (incompleted), созданные до начала периода
    in_progress = Application.query.filter(
        Application.submission_date < start_utc,
        Application.status == 'incompleted'
    ).count()

    # 2. Завершённые заявки (completed или refusal), созданные до начала периода,
    #    но обработанные (дезинфекция или отказ) в течение отчётного периода.
    #    Для статуса 'refusal' используется disinfection_date (дата оформления отказа).
    completed_or_refusal = db.session.query(Application).join(
        Disinfection, Disinfection.application_id == Application.id
    ).filter(
        Application.submission_date < start_utc,
        Application.status.in_(['completed', 'refusal']),
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).distinct().count()

    return in_progress + completed_or_refusal


def get_total_info_for_report(start_date, end_date):
    """
    Получение общей информации с использованием локальной временной зоны.
    start_date и end_date уже в Asia/Yakutsk.
    Оптимизировано: агрегация в одном запросе через JOIN + CASE WHEN.
    """
    if start_date is None or end_date is None:
        return {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'refusal': 0,
            'washes': 0
        }

    start_utc = to_utc(start_date)
    end_utc = to_utc(end_date)

    # Всего заявок по периоду подачи
    total = Application.query.filter(
        Application.submission_date.between(start_utc, end_utc)
    ).count()

    # Один запрос: JOIN с Disinfection + фильтрация по периоду дезинфекции + CASE WHEN
    result = db.session.query(
        func.count(case((Application.status == 'completed', 1))).label('completed'),
        func.count(case((Application.status == 'refusal', 1))).label('refusal'),
    ).join(
        Disinfection, Disinfection.application_id == Application.id
    ).filter(
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).first()

    completed = result.completed if result else 0
    refusal = result.refusal if result else 0

    washes = Disinfection.query.filter(
        Disinfection.disinfection_date.between(start_utc, end_utc)
    ).with_entities(db.func.sum(Disinfection.swab_testing)).scalar() or 0

    in_progress = total - completed - refusal

    return {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'refusal': refusal,
        'washes': washes
    }
