from django import template

register = template.Library()

@register.filter
def format_duration(seconds):
    """Форматирует длительность трека в формат MM:SS"""
    if not seconds:
        return "00:00"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}" 