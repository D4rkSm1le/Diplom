from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth.models import User
from .models import Track, Playlist, PlaylistTrack, UserProfile, UserLog, Album, SupportTicket, SupportMessage
from .forms import TrackUploadForm, PlaylistForm, UserRegistrationForm, UserUpdateForm, AdminTrackForm, AlbumForm, TrackFormSet
import logging
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
import qrcode
from django.urls import reverse
from io import BytesIO
import json
from django.db.models import Q, F
from .utils import create_backup, restore_backup
import os
from django.db import transaction
from datetime import timedelta, date
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import connection
from django.utils import timezone
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

def is_artist(user):
    """Проверка, является ли пользователь исполнителем"""
    return hasattr(user, 'profile') and user.profile.role == 'artist'

def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    return user.is_superuser

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_user_action(request, action, details=None):
    if request.user.is_authenticated:
        UserLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=get_client_ip(request)
        )

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Security check complete. Log the user in."""
        # Выходим из текущей сессии, если пользователь авторизован
        if self.request.user.is_authenticated:
            logout(self.request)
        
        response = super().form_valid(form)
        log_user_action(self.request, 'Вход в систему')
        messages.success(self.request, f'Добро пожаловать, {self.request.user.username}!')
        return response

class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_user_action(request, 'Выход из системы')
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
            log_user_action(request, 'Регистрация')
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
    return render(request, 'music/moderation_list.html', {
        'tracks': tracks,
        'form': AdminTrackForm()
    })

@login_required
@user_passes_test(is_admin)
def approve_track(request, pk):
    """Одобрение трека"""
    track = get_object_or_404(Track, pk=pk)
    if request.method == 'POST':
        form = AdminTrackForm(request.POST, instance=track)
        if form.is_valid():
            form.save()
            log_user_action(request, 'Одобрение трека', f'Трек: {track.title}')
            messages.success(request, f'Трек "{track.title}" одобрен')
            return redirect('music:moderation_list')
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
        log_user_action(request, 'Отклонение трека', f'Трек: {track_title}, Комментарий: {comment}')
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
            Q(album__title__icontains=query)  # Добавляем поиск по названию альбома
        )
    
    # Применяем сортировку
    if sort_by == 'popular':
        tracks = tracks.order_by('-play_count', '-created_at')
    elif sort_by == 'alphabetical':
        tracks = tracks.order_by('title', 'artist')
    else:  # 'recent' - сортировка по дате добавления (по умолчанию)
        tracks = tracks.order_by('-created_at')
    
    # Получаем плейлисты пользователя
    user_playlists = Playlist.objects.filter(user=request.user) if request.user.is_authenticated else []
    
    context = {
        'tracks': tracks,
        'user_playlists': user_playlists,
        'current_sort': sort_by,
        'query': query
    }
    
    return render(request, 'music/track_list.html', context)

def check_age_restriction(user, track):
    """Проверяет, может ли пользователь получить доступ к треку с цензурой"""
    if not track.is_explicit:
        return True
        
    if not user.is_authenticated:
        return False
        
    try:
        profile = user.profile
        if not profile.birth_date:
            return False
            
        today = date.today()
        age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
        return age >= 18
    except UserProfile.DoesNotExist:
        return False

@login_required
def track_detail(request, pk):
    """Детальная информация о треке"""
    track = get_object_or_404(Track, pk=pk)
    
    if not check_age_restriction(request.user, track):
        raise PermissionDenied("Вам должно быть 18 лет для доступа к этому треку")
        
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
                    duration_seconds = int(audio.info.length)
                    track.duration = timedelta(seconds=duration_seconds)
                    print(f"Track {track.title} duration: {duration_seconds} seconds, timedelta: {track.duration}")
            except Exception as e:
                logger.error(f"Ошибка при определении длительности трека: {str(e)}")
                track.duration = timedelta(seconds=0)
                print(f"Error getting duration for track {track.title}: {str(e)}")
            
            track.save()
            print(f"Saved track {track.title} with duration {track.duration}")
            
            log_user_action(request, 'Загрузка трека', f'Трек: {track.title}')
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

@require_POST
def increment_play_count(request, track_id):
    """Увеличивает счетчик прослушиваний трека"""
    print(f"SQL: Увеличиваем счетчик для трека {track_id}")
    
    try:
        # Используем прямой SQL-запрос для увеличения счетчика
        with connection.cursor() as cursor:
            # В PostgreSQL можно было бы использовать RETURNING, но для совместимости с SQLite
            # мы сначала обновляем, а затем запрашиваем значение
            cursor.execute(
                "UPDATE music_track SET play_count = play_count + 1 WHERE id = %s", 
                [track_id]
            )
            
            # Запрашиваем обновленное значение
            cursor.execute(
                "SELECT play_count FROM music_track WHERE id = %s",
                [track_id]
            )
            
            result = cursor.fetchone()
            if result:
                new_count = result[0]
                print(f"SQL: Счетчик трека {track_id} увеличен до {new_count}")
                
                return JsonResponse({
                    'success': True,
                    'play_count': new_count
                })
            else:
                print(f"SQL: Трек {track_id} не найден")
                return JsonResponse({
                    'success': False,
                    'error': 'Трек не найден'
                }, status=404)
    except Exception as e:
        print(f"SQL: Ошибка при увеличении счетчика: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@ensure_csrf_cookie
def get_playlists(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    playlists = Playlist.objects.filter(user=request.user)
    playlists_data = [{
        'id': playlist.id,
        'name': playlist.name,
        'track_count': playlist.tracks.count()
    } for playlist in playlists]
    
    return JsonResponse(playlists_data, safe=False)

@require_POST
@ensure_csrf_cookie
def add_track_to_playlist(request, playlist_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        track_id = data.get('track_id')
        
        if not track_id:
            return JsonResponse({
                'success': False,
                'error': 'Не указан ID трека'
            }, status=400)
        
        playlist = get_object_or_404(Playlist, pk=playlist_id, user=request.user)
        track = get_object_or_404(Track, pk=track_id)
        
        if track in playlist.tracks.all():
            return JsonResponse({
                'success': False,
                'error': 'Трек уже есть в плейлисте'
            })
        
        playlist.tracks.add(track)
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

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
    popular_tracks = Track.objects.filter(is_approved=True).order_by('-play_count')
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

@login_required
def settings_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Имя пользователя успешно обновлено!')
            return redirect('music:settings')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'music/settings.html', {
        'user': request.user,
        'form': form
    })

@login_required
@user_passes_test(is_admin)
def backup_system(request):
    """Создание резервной копии системы"""
    try:
        backup_file = create_backup()
        file_path = os.path.join(settings.BASE_DIR, 'backups', backup_file)
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{backup_file}"'
        return response
    except Exception as e:
        messages.error(request, f'Ошибка при создании резервной копии: {str(e)}')
        return redirect('music:admin_panel')

@login_required
@user_passes_test(is_admin)
def restore_system(request):
    """Восстановление системы из резервной копии"""
    if request.method == 'POST' and request.FILES.get('backup_file'):
        try:
            backup_file = request.FILES['backup_file']
            temp_path = os.path.join(settings.BASE_DIR, 'temp_backup.zip')
            
            # Сохраняем загруженный файл
            with open(temp_path, 'wb+') as destination:
                for chunk in backup_file.chunks():
                    destination.write(chunk)
            
            # Восстанавливаем систему
            restore_backup(temp_path)
            
            # Удаляем временный файл
            os.remove(temp_path)
            
            messages.success(request, 'Система успешно восстановлена из резервной копии')
        except Exception as e:
            messages.error(request, f'Ошибка при восстановлении системы: {str(e)}')
        return redirect('music:admin_panel')
    
    return render(request, 'music/restore_backup.html')

@login_required
def album_list(request):
    albums = Album.objects.all().order_by('-created_at')
    return render(request, 'music/album_list.html', {'albums': albums})

@login_required
def album_detail(request, pk):
    album = get_object_or_404(Album, pk=pk)
    user_playlists = Playlist.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'music/album_detail.html', {
        'album': album,
        'user_playlists': user_playlists
    })

@login_required
def album_create(request):
    if request.method == 'POST':
        form = AlbumForm(request.POST, request.FILES)
        formset = TrackFormSet(request.POST, request.FILES, prefix='tracks')
        
        if form.is_valid() and formset.is_valid():
            album = form.save(commit=False)
            album.user = request.user
            album.save()
            
            tracks = formset.save(commit=False)
            for track in tracks:
                track.album = album
                track.user = request.user
                track.is_approved = True  # Автоматически одобряем треки
                track.artist = album.artist  # Используем артиста альбома
                
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
                        track.duration = timedelta(seconds=int(audio.info.length))
                except Exception as e:
                    logger.error(f"Ошибка при определении длительности трека: {str(e)}")
                    track.duration = timedelta(seconds=0)
                
                track.save()
            
            messages.success(request, 'Альбом успешно создан.')
            return redirect('music:album_detail', pk=album.pk)
    else:
        form = AlbumForm()
        formset = TrackFormSet(prefix='tracks')
    
    return render(request, 'music/album_form.html', {
        'form': form,
        'formset': formset,
        'album': None
    })

@login_required
def album_edit(request, pk):
    album = get_object_or_404(Album, pk=pk)
    
    if album.user != request.user and not request.user.is_superuser:
        messages.error(request, 'У вас нет прав на редактирование этого альбома.')
        return redirect('music:album_detail', pk=album.pk)
    
    if request.method == 'POST':
        form = AlbumForm(request.POST, request.FILES, instance=album)
        formset = TrackFormSet(request.POST, request.FILES, prefix='tracks', instance=album)
        
        if form.is_valid() and formset.is_valid():
            album = form.save()
            tracks = formset.save(commit=False)
            
            for track in tracks:
                track.album = album
                track.user = request.user
                track.is_approved = True  # Автоматически одобряем треки
                track.artist = album.artist  # Используем артиста альбома
                
                # Определяем длительность трека если это новый файл
                if track.audio_file and hasattr(track.audio_file, 'path'):
                    try:
                        audio_path = track.audio_file.path
                        if audio_path.lower().endswith('.mp3'):
                            audio = MP3(audio_path)
                        elif audio_path.lower().endswith('.wav'):
                            audio = WAVE(audio_path)
                        else:
                            audio = File(audio_path)
                        
                        if hasattr(audio, 'info'):
                            track.duration = timedelta(seconds=int(audio.info.length))
                    except Exception as e:
                        logger.error(f"Ошибка при определении длительности трека: {str(e)}")
                        track.duration = timedelta(seconds=0)
                
                track.save()
            
            # Сохраняем удаленные треки из формсета
            for deleted_object in formset.deleted_objects:
                deleted_object.delete()
            
            messages.success(request, 'Альбом успешно обновлен.')
            return redirect('music:album_detail', pk=album.pk)
    else:
        form = AlbumForm(instance=album)
        formset = TrackFormSet(prefix='tracks', instance=album)
    
    return render(request, 'music/album_form.html', {
        'form': form,
        'formset': formset,
        'album': album
    })

@login_required
@user_passes_test(is_admin)  # Только администратор может удалять альбомы
def album_delete(request, pk):
    """Удаление альбома"""
    album = get_object_or_404(Album, pk=pk)
    
    if request.method == 'POST':
        album_title = album.title
        album.delete()
        log_user_action(request, 'Удаление альбома', f'Альбом: {album_title}')
        messages.success(request, f'Альбом "{album_title}" успешно удален')
        return redirect('music:album_list')
    
    return redirect('music:album_detail', pk=pk)

@login_required
def add_to_playlist(request):
    if request.method == 'POST':
        track_id = request.POST.get('track_id')
        playlist_id = request.POST.get('playlist_id')
        
        try:
            track = Track.objects.get(id=track_id)
            playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            
            if track not in playlist.tracks.all():
                playlist.tracks.add(track)
                messages.success(request, 'Трек успешно добавлен в плейлист!')
            else:
                messages.info(request, 'Этот трек уже есть в плейлисте')
                
        except (Track.DoesNotExist, Playlist.DoesNotExist):
            messages.error(request, 'Ошибка при добавлении трека в плейлист')
            
    return redirect(request.META.get('HTTP_REFERER', 'music:track_list'))

@login_required
def support_ticket_list(request):
    """Список тикетов пользователя или все тикеты для админа"""
    if request.user.is_superuser:
        tickets = SupportTicket.objects.all()
    else:
        tickets = SupportTicket.objects.filter(user=request.user)
    return render(request, 'music/support/ticket_list.html', {'tickets': tickets})

@login_required
def support_ticket_create(request):
    """Создание нового тикета"""
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if subject and message:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject
            )
            SupportMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=message
            )
            messages.success(request, 'Тикет успешно создан')
            return redirect('music:support_ticket_detail', pk=ticket.pk)
    return render(request, 'music/support/ticket_create.html')

@login_required
def support_ticket_detail(request, pk):
    """Детальная информация о тикете"""
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if not request.user.is_superuser and ticket.user != request.user:
        messages.error(request, 'У вас нет доступа к этому тикету')
        return redirect('music:support_ticket_list')
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            message = SupportMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=message_text
            )
            ticket.updated_at = timezone.now()
            ticket.save()
            return JsonResponse({
                'status': 'success',
                'message_id': message.id
            })
        return JsonResponse({'status': 'error', 'error': 'Сообщение не может быть пустым'})
    
    messages = ticket.messages.all()
    return render(request, 'music/support/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages
    })

@login_required
@user_passes_test(is_admin)
def support_ticket_update_status(request, pk):
    """Обновление статуса тикета (только для админа)"""
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(SupportTicket.STATUS_CHOICES):
            ticket.status = new_status
            ticket.save()
            messages.success(request, 'Статус тикета обновлен')
    return redirect('music:support_ticket_detail', pk=pk)

@login_required
def get_new_messages(request, ticket_id):
    """Получение новых сообщений для тикета (AJAX)"""
    ticket = get_object_or_404(SupportTicket, pk=ticket_id)
    if not request.user.is_superuser and ticket.user != request.user:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    last_message_id = request.GET.get('last_message_id', 0)
    new_messages = ticket.messages.filter(id__gt=last_message_id)
    
    messages_data = [{
        'id': msg.id,
        'user': msg.user.username,
        'message': msg.message,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in new_messages]
    
    return JsonResponse({'messages': messages_data})

def permission_denied_view(request, exception):
    """Представление для обработки ошибки 403 (доступ запрещен)"""
    return render(request, '403.html', {'exception': str(exception)}, status=403)
