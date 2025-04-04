from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def type(value):
    """Возвращает тип объекта"""
    return value.__class__.__name__

@register.filter(name='format_duration')
def format_duration(value):
    """
    Форматирует длительность в формат MM:SS
    """
    if value is None:
        return "00:00"
        
    try:
        if isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
        elif isinstance(value, (int, float)):
            total_seconds = int(value)
        elif isinstance(value, str):
            if ':' in value:
                minutes, seconds = map(int, value.split(':'))
                total_seconds = minutes * 60 + seconds
            else:
                total_seconds = int(float(value))
        else:
            print(f"Unexpected duration type: {type(value)}, value: {value}")  # Для отладки
            return "00:00"

        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    except Exception as e:
        print(f"Error formatting duration: {str(e)}, value: {value}, type: {type(value)}")  # Для отладки
        return "00:00" 