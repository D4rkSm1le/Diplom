from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth.models import User
from .models import Track, Playlist, PlaylistTrack, UserProfile
from .forms import TrackUploadForm, PlaylistForm, UserRegistrationForm
import logging
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
import qrcode
from django.urls import reverse
from io import BytesIO
import json
from django.db.models import Q, F

logger = logging.getLogger(__name__)

def is_artist(user):
    """Проверка, является ли пользователь исполнителем"""
    return hasattr(user, 'profile') and user.profile.role == 'artist'

def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    return user.is_superuser

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Security check complete. Log the user in."""
        # Выходим из текущей сессии, если пользователь авторизован
        if self.request.user.is_authenticated:
            logout(self.request)
        
        response = super().form_valid(form)
        messages.success(self.request, f'Добро пожаловать, {self.request.user.username}!')
        return response

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, 'Вы успешно вышли из системы')
        return response

def register(request):
    if request.user.is_authenticated:
        return redirect('music:home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('music:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def moderation_list(request):
    """Список треков на модерации"""
    tracks = Track.objects.filter(is_approved=False)
    return render(request, 'music/moderation_list.html', {'tracks': tracks})

@login_required
@user_passes_test(is_admin)
def approve_track(request, pk):
    """Одобрение трека"""
    track = get_object_or_404(Track, pk=pk)
    track.is_approved = True
    track.save()
    messages.success(request, f'Трек "{track.title}" одобрен')
    return redirect('music:moderation_list')

@login_required
@user_passes_test(is_admin)
def reject_track(request, pk):
    """Отклонение трека"""
    track = get_object_or_404(Track, pk=pk)
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        # Сохраняем информацию о треке для уведомления пользователя
        track_title = track.title
        # Удаляем трек
        track.delete()
        messages.warning(request, f'Трек "{track_title}" отклонен и удален')
        return redirect('music:moderation_list')
    return render(request, 'music/reject_track.html', {'track': track})

def track_list(request):
    """Список всех треков с поддержкой поиска и фильтрации"""
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'recent')  # По умолчанию сортируем по дате добавления
    
    # Базовый запрос для треков
    tracks = Track.objects.filter(is_approved=True)
    
    # Применяем поиск, если указан
    if query:
        tracks = tracks.filter(
            Q(title__icontains=query) |
            Q(artist__icontains=query) |
            Q(album__icontains=query)
        )
    
    # Применяем сортировку
    if sort_by == 'popular':
        tracks = tracks.order_by('-play_count', '-created_at')
    elif sort_by == 'alphabetical':
        tracks = tracks.order_by('title', 'artist')
    else:  # 'recent' - сортировка по дате добавления (по умолчанию)
        tracks = tracks.order_by('-created_at')
    
    user_playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'music/track_list.html', {
        'tracks': tracks,
        'user_playlists': user_playlists,
        'current_sort': sort_by,
        'query': query
    })

@login_required
def track_detail(request, pk):
    """Детальная информация о треке"""
    track = get_object_or_404(Track, pk=pk)
    user_playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'music/track_detail.html', {
        'track': track,
        'user_playlists': user_playlists
    })

@login_required
@user_passes_test(is_artist)
def my_tracks(request):
    """Список треков исполнителя"""
    tracks = Track.objects.filter(user=request.user)
    return render(request, 'music/my_tracks.html', {'tracks': tracks})

@login_required
def track_upload(request):
    """Загрузка трека"""
    if request.method == 'POST':
        form = TrackUploadForm(request.POST, request.FILES)
        if form.is_valid():
            track = form.save(commit=False)
            track.user = request.user
            track.is_approved = False
            
            # Если пользователь не артист, добавляем пометку в название
            if not is_artist(request.user):
                track.title = f"{track.title} (от слушателя {request.user.username})"
            
            track.save()
            
            # Определяем длительность трека
            try:
                audio_path = track.audio_file.path
                if audio_path.lower().endswith('.mp3'):
                    audio = MP3(audio_path)
                elif audio_path.lower().endswith('.wav'):
                    audio = WAVE(audio_path)
                else:
                    audio = File(audio_path)
                
                if hasattr(audio, 'info'):
                    track.duration = int(audio.info.length)
                    track.save()
            except Exception as e:
                logger.error(f"Ошибка при определении длительности трека: {str(e)}")
                track.duration = 0
                track.save()
            
            messages.success(request, 'Трек отправлен на модерацию')
            return redirect('music:track_list')
    else:
        form = TrackUploadForm()
    
    return render(request, 'music/track_upload.html', {'form': form})

@login_required
def playlist_list(request):
    """Список плейлистов пользователя"""
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, 'music/playlist_list.html', {'playlists': playlists})

@login_required
def playlist_detail(request, pk):
    """Детальная информация о плейлисте"""
    playlist = get_object_or_404(Playlist, pk=pk, user=request.user)
    return render(request, 'music/playlist_detail.html', {'playlist': playlist})

@login_required
def playlist_create(request):
    """Создание нового плейлиста"""
    if request.method == 'POST':
        form = PlaylistForm(request.POST)
        if form.is_valid():
            playlist = form.save(commit=False)
            playlist.user = request.user
            playlist.save()
            messages.success(request, 'Плейлист успешно создан')
            return redirect('music:playlist_detail', pk=playlist.pk)
    else:
        form = PlaylistForm()
    
    return render(request, 'music/playlist_form.html', {'form': form, 'title': 'Создание плейлиста'})

@login_required
def playlist_edit(request, pk):
    """Редактирование плейлиста"""
    playlist = get_object_or_404(Playlist, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            form.save()
            messages.success(request, 'Плейлист успешно обновлен')
            return redirect('music:playlist_detail', pk=playlist.pk)
    else:
        form = PlaylistForm(instance=playlist)
    
    return render(request, 'music/playlist_form.html', {'form': form, 'title': 'Редактирование плейлиста'})

@login_required
def playlist_delete(request, pk):
    """Удаление плейлиста"""
    playlist = get_object_or_404(Playlist, pk=pk, user=request.user)
    if request.method == 'POST':
        playlist.delete()
        messages.success(request, 'Плейлист успешно удален')
        return redirect('music:playlist_list')
    
    return render(request, 'music/playlist_confirm_delete.html', {'playlist': playlist})

@login_required
@require_POST
def add_track_to_playlist(request):
    """Добавление трека в плейлист"""
    try:
        track_id = request.POST.get('track_id')
        playlist_id = request.POST.get('playlist_id')
        
        if not track_id or not playlist_id:
            return JsonResponse({'error': 'Не указан трек или плейлист'}, status=400)
        
        track = get_object_or_404(Track, pk=track_id)
        playlist = get_object_or_404(Playlist, pk=playlist_id, user=request.user)
        
        # Проверяем, нет ли уже этого трека в плейлисте
        if not PlaylistTrack.objects.filter(playlist=playlist, track=track).exists():
            PlaylistTrack.objects.create(playlist=playlist, track=track)
            return JsonResponse({'message': 'Трек успешно добавлен в плейлист'})
        else:
            return JsonResponse({'error': 'Этот трек уже есть в плейлисте'}, status=400)
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении трека в плейлист: {str(e)}")
        return JsonResponse({'error': 'Ошибка при добавлении трека в плейлист'}, status=500)

def generate_qr(request, pk):
    track = get_object_or_404(Track, pk=pk)
    
    # Создаем прямую ссылку на трек
    track_url = request.build_absolute_uri(reverse('music:track_detail', args=[pk]))
    
    # Создаем QR-код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(track_url)
    qr.make(fit=True)

    # Создаем изображение QR-кода
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Сохраняем изображение в буфер
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Возвращаем изображение как HTTP-ответ
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="track_{pk}_qr.png"'
    return response

def home(request):
    """Главная страница с популярными треками"""
    popular_tracks = Track.objects.order_by('-play_count')[:10]
    return render(request, 'music/home.html', {'tracks': popular_tracks})

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    """Панель администратора"""
    context = {
        'pending_tracks_count': Track.objects.filter(is_approved=False).count(),
        'total_tracks_count': Track.objects.count(),
        'total_users_count': User.objects.count(),
        'pending_tracks': Track.objects.filter(is_approved=False).order_by('-created_at')[:10],
    }
    return render(request, 'music/admin_panel.html', context)

@require_POST
def increment_play_count(request, pk):
    track = get_object_or_404(Track, pk=pk)
    # Увеличиваем счетчик при каждом вызове функции
    track.play_count = F('play_count') + 1
    track.save(update_fields=['play_count'])
    # Получаем обновленное значение
    track.refresh_from_db()
    return JsonResponse({'play_count': track.play_count})
