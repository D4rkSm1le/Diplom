from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class UserProfile(models.Model):
    """Модель профиля пользователя с ролью"""
    ROLES = (
        ('listener', 'Слушатель'),
        ('artist', 'Исполнитель'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLES, default='listener', verbose_name='Роль')
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'

class Playlist(models.Model):
    """Модель для хранения информации о плейлисте"""
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    cover = models.ImageField(upload_to='playlist_covers/', blank=True, null=True, verbose_name='Обложка')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    tracks = models.ManyToManyField('Track', through='PlaylistTrack', verbose_name='Треки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Track(models.Model):
    """Модель для хранения информации о треке"""
    title = models.CharField(max_length=200, verbose_name='Название')
    artist = models.CharField(max_length=200, verbose_name='Исполнитель')
    album = models.CharField(max_length=200, blank=True, null=True, verbose_name='Альбом')
    audio_file = models.FileField(upload_to='tracks/', verbose_name='Аудио файл', blank=True, null=True)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name='Обложка')
    duration = models.IntegerField(default=0, verbose_name='Длительность (сек)')
    play_count = models.IntegerField(default=0, verbose_name='Количество прослушиваний')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    moderation_comment = models.TextField(blank=True, null=True, verbose_name='Комментарий модератора')

    class Meta:
        verbose_name = 'Трек'
        verbose_name_plural = 'Треки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.artist}'

class PlaylistTrack(models.Model):
    """Промежуточная модель для связи плейлиста и трека"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, verbose_name='Плейлист')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, verbose_name='Трек')
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Трек в плейлисте'
        verbose_name_plural = 'Треки в плейлистах'
        ordering = ['position']
        unique_together = ['playlist', 'track']

    def __str__(self):
        return f"{self.track.title} в плейлисте {self.playlist.name}"
