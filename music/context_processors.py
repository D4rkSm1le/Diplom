from .models import Track

def pending_tracks_count(request):
    """Добавляет количество треков на модерации в контекст шаблона"""
    if request.user.is_authenticated and request.user.is_superuser:
        return {'pending_tracks_count': Track.objects.filter(is_approved=False).count()}
    return {'pending_tracks_count': 0} 