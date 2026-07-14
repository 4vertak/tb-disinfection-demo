import json
from datetime import datetime, date
from decimal import Decimal

def json_serializer(obj):
    """Кастомный JSON сериализатор для datetime и других типов"""
    
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return {
            key: value for key, value in obj.__dict__.items()
            if not key.startswith('_') and not hasattr(value, '__dict__')
        }
    raise TypeError(f"Type {type(obj)} not serializable")