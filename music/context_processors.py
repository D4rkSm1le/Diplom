from .models import Track, SupportTicket, SupportMessage

def pending_tracks_count(request):
    """Добавляет количество треков на модерации в контекст шаблона"""
    if request.user.is_authenticated and request.user.is_superuser:
        return {'pending_tracks_count': Track.objects.filter(is_approved=False).count()}
    return {'pending_tracks_count': 0}

def support_tickets_count(request):
    """Контекстный процессор для подсчета непрочитанных тикетов"""
    if request.user.is_authenticated and request.user.is_superuser:
        # Для админа считаем все непрочитанные сообщения в открытых тикетах
        unread_count = SupportMessage.objects.filter(
            ticket__status__in=['open', 'in_progress'],
            is_read=False
        ).exclude(user=request.user).count()
    else:
        unread_count = 0
    
    return {'unread_tickets_count': unread_count} 