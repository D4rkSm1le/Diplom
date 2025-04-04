from django.contrib import admin
from django.utils.html import format_html
from .models import Track, Playlist, PlaylistTrack, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'get_email')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'artist', 'user', 'created_at', 'is_approved', 'play_count', 'get_audio_player', 'get_cover')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title', 'artist', 'album')
    list_editable = ('title', 'artist')
    actions = ['approve_tracks', 'reject_tracks']
    
    # Добавляем поля для редактирования
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'artist', 'album', 'user', 'duration', 'play_count')
        }),
        ('Медиафайлы', {
            'fields': ('audio_file', 'cover')
        }),
        ('Модерация', {
            'fields': ('is_approved', 'moderation_comment')
        }),
    )
    
    def get_audio_player(self, obj):
        if obj.audio_file:
            return format_html('<audio controls><source src="{}" type="audio/mpeg"></audio>', obj.audio_file.url)
        return "Нет аудио"
    get_audio_player.short_description = 'Прослушать'
    
    def get_cover(self, obj):
        if obj.cover:
            return format_html('<img src="{}" width="50" height="50" />', obj.cover.url)
        return "Нет обложки"
    get_cover.short_description = 'Обложка'
    
    def approve_tracks(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'Выбранные треки ({queryset.count()}) были одобрены')
    approve_tracks.short_description = 'Одобрить выбранные треки'
    
    def reject_tracks(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'Выбранные треки ({queryset.count()}) были отклонены')
    reject_tracks.short_description = 'Отклонить выбранные треки'

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'get_tracks_count', 'get_cover')
    search_fields = ('name', 'description')
    
    def get_tracks_count(self, obj):
        return obj.tracks.count()
    get_tracks_count.short_description = 'Количество треков'
    
    def get_cover(self, obj):
        if obj.cover:
            return format_html('<img src="{}" width="50" height="50" />', obj.cover.url)
        return "Нет обложки"
    get_cover.short_description = 'Обложка'

@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'track', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('playlist__name', 'track__title')
