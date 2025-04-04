import os
import json
import shutil
from datetime import datetime
from django.conf import settings
from django.core import serializers
from .models import Track, Playlist, PlaylistTrack, UserProfile
from django.contrib.auth.models import User

def create_backup():
    """Создание резервной копии системы"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(settings.BASE_DIR, 'backups', timestamp)
    os.makedirs(backup_dir, exist_ok=True)

    # Создаем копию медиафайлов
    media_backup_dir = os.path.join(backup_dir, 'media')
    if os.path.exists(settings.MEDIA_ROOT):
        shutil.copytree(settings.MEDIA_ROOT, media_backup_dir)

    # Сохраняем данные моделей
    models = [User, UserProfile, Track, Playlist, PlaylistTrack]
    for model in models:
        data = serializers.serialize('json', model.objects.all())
        filename = f'{model.__name__.lower()}.json'
        with open(os.path.join(backup_dir, filename), 'w', encoding='utf-8') as f:
            f.write(data)

    # Создаем архив
    archive_name = f'backup_{timestamp}'
    shutil.make_archive(os.path.join(settings.BASE_DIR, 'backups', archive_name), 
                       'zip', backup_dir)
    
    # Удаляем временную директорию
    shutil.rmtree(backup_dir)
    
    return f'{archive_name}.zip'

def restore_backup(backup_file):
    """Восстановление системы из резервной копии"""
    # Создаем временную директорию для распаковки
    temp_dir = os.path.join(settings.BASE_DIR, 'temp_backup')
    os.makedirs(temp_dir, exist_ok=True)

    # Распаковываем архив
    shutil.unpack_archive(backup_file, temp_dir, 'zip')

    # Восстанавливаем медиафайлы
    media_backup_dir = os.path.join(temp_dir, 'media')
    if os.path.exists(media_backup_dir):
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
        shutil.copytree(media_backup_dir, settings.MEDIA_ROOT)

    # Восстанавливаем данные моделей
    models = [User, UserProfile, Track, Playlist, PlaylistTrack]
    for model in models:
        filename = os.path.join(temp_dir, f'{model.__name__.lower()}.json')
        if os.path.exists(filename):
            model.objects.all().delete()  # Очищаем существующие данные
            with open(filename, 'r', encoding='utf-8') as f:
                data = serializers.deserialize('json', f.read())
                for obj in data:
                    obj.save()

    # Удаляем временную директорию
    shutil.rmtree(temp_dir) 