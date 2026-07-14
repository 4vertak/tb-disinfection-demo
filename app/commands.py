import click
from flask.cli import with_appcontext
from sqlalchemy import text


@click.command('init-application-numbers')
@click.option('--dry-run', is_flag=True, help='Показать что будет сделано без реального выполнения')
@click.option('--year', type=int, help='Инициализировать только указанный год')
@with_appcontext
def init_application_numbers_command(dry_run, year):
    """Команда для инициализации номеров существующих заявок"""
    from .domain.services.application_number_service import ApplicationNumberService
    from .domain.models.application.entities import Application
    from .utils.date_utils import to_local
    
    try:
        if dry_run:
            click.echo("Режим предпросмотра (dry-run)...")
            
            # Анализ существующих данных
            applications = Application.query.filter(Application.application_number.is_(None))
            if year:
                applications = [app for app in applications if app.submission_date and to_local(app.submission_date).year == year]
            
            click.echo(f"Найдено {applications.count()} заявок без номеров")
            
            # Группировка по годам
            years_data = {}
            for app in applications:
                if app.submission_date:
                    app_year = to_local(app.submission_date).year
                    if app_year not in years_data:
                        years_data[app_year] = []
                    years_data[app_year].append(app)
            
            for year, apps in years_data.items():
                click.echo(f"  {year} год: {len(apps)} заявок")
                
            click.echo("Dry-run завершен. Для реального выполнения уберите --dry-run")
            return
        
        # Реальное выполнение
        click.echo("Начало инициализации номеров заявок...")
        
        result = ApplicationNumberService.initialize_existing_applications(year)
        click.echo(f"{result}")
        
        # Проверка результатов
        total_with_numbers = Application.query.filter(Application.application_number.isnot(None)).count()
        total_without_numbers = Application.query.filter(Application.application_number.is_(None)).count()
        
        click.echo(f"Итоги:")
        click.echo(f"   Заявок с номерами: {total_with_numbers}")
        click.echo(f"   Заявок без номеров: {total_without_numbers}")
        
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)
        raise click.Abort()


@click.command('check-application-numbers')
@with_appcontext
def check_application_numbers_command():
    """Проверить статус номеров заявок"""
    from .domain.models.application.entities import Application
    from .domain.models.application.entities import ApplicationCounter
    
    try:
        click.echo("Проверка статуса номеров заявок...")
        
        # Статистика по заявкам
        total_applications = Application.query.count()
        applications_with_numbers = Application.query.filter(Application.application_number.isnot(None)).count()
        applications_without_numbers = Application.query.filter(Application.application_number.is_(None)).count()
        
        click.echo(f"Общая статистика:")
        click.echo(f"   Всего заявок: {total_applications}")
        click.echo(f"   С номерами: {applications_with_numbers}")
        click.echo(f"   Без номеров: {applications_without_numbers}")
        
        # Статистика по счетчикам
        counters = ApplicationCounter.query.all()
        click.echo(f"Счетчики по годам:")
        for counter in counters:
            click.echo(f"   {counter.year}: последний номер = {counter.last_number}")
        
        if applications_without_numbers > 0:
            click.echo("Есть заявки без номеров. Запустите 'flask init-application-numbers'")
        else:
            click.echo("Все заявки имеют номера")
            
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)


@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Создать администратора по умолчанию"""
    from .domain.services.user_service import UserInitializer
    try:
        result = UserInitializer.create_admin_account()
        if result:
            click.echo("Администратор создан")
        else:
            click.echo("Администратор уже существует")
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)


@click.command('fill-directories')
@with_appcontext
def fill_directories_command():
    """Заполнить системные справочники"""
    from .domain.services.user_service import UserInitializer
    try:
        UserInitializer.fill_directories()
        click.echo("Справочники заполнены")
    except Exception as e:
        click.echo(f"Ошибка: {str(e)}", err=True)

@click.command('cleanup-notifications')
@click.option('--days', default=30, help='Удалять уведомления старше указанного количества дней')
@with_appcontext
def cleanup_notifications_command(days):
    """Команда для очистки старых прочитанных уведомлений"""
    from app.domain.services.notification_service import NotificationService
    
    try:
        deleted_count = NotificationService.cleanup_read_notifications(days)
        click.echo(f"Удалено {deleted_count} прочитанных уведомлений старше {days} дней")
    except Exception as e:
        click.echo(f"Ошибка при очистке уведомлений: {str(e)}", err=True)


def init_app(app):
    """Инициализация команд приложения"""
    app.cli.add_command(init_application_numbers_command)
    app.cli.add_command(check_application_numbers_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(fill_directories_command)
    app.cli.add_command(cleanup_notifications_command) 