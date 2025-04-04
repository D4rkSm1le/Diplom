from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError

def validate_audio_file(value):
    ext = value.name.split('.')[-1]
    valid_extensions = ['mp3', 'wav', 'ogg']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Поддерживаются только аудио файлы (mp3, wav, ogg)')

class UserProfile(models.Model):
    """Модель профиля пользователя с ролью"""
    ROLES = (
        ('listener', 'Слушатель'),
        ('artist', 'Исполнитель'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLES, default='listener', verbose_name='Роль')
    birth_date = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    
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

class Album(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    artist = models.CharField(max_length=200, verbose_name='Исполнитель')
    cover = models.ImageField(upload_to='album_covers/', null=True, blank=True, verbose_name='Обложка')
    release_date = models.DateField(verbose_name='Дата выпуска')
    description = models.TextField(blank=True, verbose_name='Описание')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Альбом'
        verbose_name_plural = 'Альбомы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.artist}'

    def get_absolute_url(self):
        return reverse('music:album_detail', kwargs={'pk': self.pk})

class Track(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    artist = models.CharField(max_length=200, verbose_name='Исполнитель')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='tracks', null=True, blank=True, verbose_name='Альбом')
    track_number = models.PositiveIntegerField(null=True, blank=True, verbose_name='Номер трека')
    audio_file = models.FileField(upload_to='tracks/', validators=[validate_audio_file], null=True, blank=True, verbose_name='Аудио файл')
    cover = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name='Обложка')
    duration = models.DurationField(null=True, blank=True, verbose_name='Длительность')
    play_count = models.PositiveIntegerField(default=0, verbose_name='Количество прослушиваний')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    moderation_comment = models.TextField(null=True, blank=True, verbose_name='Комментарий модератора')

    class Meta:
        verbose_name = 'Трек'
        verbose_name_plural = 'Треки'
        ordering = ['album', 'track_number', '-created_at']

    def __str__(self):
        return f'{self.title} - {self.artist}'

    def get_absolute_url(self):
        return reverse('music:track_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.artist and self.album:
            self.artist = self.album.artist
        super().save(*args, **kwargs)

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

class UserLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Лог пользователя'
        verbose_name_plural = 'Логи пользователей'

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.created_at})"
