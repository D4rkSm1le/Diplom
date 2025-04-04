from django.contrib import admin
from django.utils.html import format_html
from .models import Track, Playlist, PlaylistTrack, UserProfile, UserLog, Album

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'user', 'is_approved', 'play_count', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('title', 'artist', 'user__username')
    readonly_fields = ('title', 'artist', 'audio_file', 'cover', 'duration', 'play_count', 'user', 'created_at')
    fields = ('title', 'artist', 'album', 'audio_file', 'cover', 'duration', 'play_count', 'user', 'created_at', 'is_approved', 'moderation_comment')

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

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

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'track', 'position')
    list_filter = ('playlist',)
    ordering = ('playlist', 'position')

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('user__username', 'action', 'details', 'ip_address')
    readonly_fields = ('user', 'action', 'details', 'ip_address', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'user', 'created_at')
    list_filter = ('release_date', 'created_at')
    search_fields = ('title', 'artist', 'description')
    date_hierarchy = 'release_date'
    readonly_fields = ('user', 'created_at')
