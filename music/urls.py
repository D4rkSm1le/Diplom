from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'music'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(next_page='music:home'), name='logout'),
    
    # Админка
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('backup/', views.backup_system, name='backup_system'),
    path('restore/', views.restore_system, name='restore_system'),
    
    # Треки
    path('tracks/', views.track_list, name='track_list'),
    path('tracks/<int:pk>/', views.track_detail, name='track_detail'),
    path('tracks/upload/', views.track_upload, name='track_upload'),
    path('tracks/<int:pk>/generate-qr/', views.generate_qr, name='generate_qr'),
    path('tracks/<int:pk>/increment-play-count/', views.increment_play_count, name='increment_play_count'),
    path('my-tracks/', views.my_tracks, name='my_tracks'),
    
    # Модерация
    path('moderation/', views.moderation_list, name='moderation_list'),
    path('moderation/<int:pk>/approve/', views.approve_track, name='approve_track'),
    path('moderation/<int:pk>/reject/', views.reject_track, name='reject_track'),
    
    # Плейлисты
    path('playlists/', views.playlist_list, name='playlist_list'),
    path('playlists/create/', views.playlist_create, name='playlist_create'),
    path('playlists/<int:pk>/', views.playlist_detail, name='playlist_detail'),
    path('playlists/<int:pk>/edit/', views.playlist_edit, name='playlist_edit'),
    path('playlists/<int:pk>/delete/', views.playlist_delete, name='playlist_delete'),
    path('settings/', views.settings_view, name='settings'),
    
    # Альбомы
    path('albums/', views.album_list, name='album_list'),
    path('albums/create/', views.album_create, name='album_create'),
    path('albums/<int:pk>/', views.album_detail, name='album_detail'),
    path('albums/<int:pk>/edit/', views.album_edit, name='album_edit'),
    path('albums/<int:pk>/delete/', views.album_delete, name='album_delete'),
    
    # API endpoints
    path('api/tracks/<int:track_id>/increment_plays/', views.increment_play_count, name='increment_play_count'),
    path('api/playlists/', views.get_playlists, name='get_playlists'),
    path('api/playlists/<int:playlist_id>/add_track/', views.add_track_to_playlist, name='add_track_to_playlist'),
    path('add-to-playlist/', views.add_to_playlist, name='add_to_playlist'),
    
    # Техническая поддержка
    path('support/', views.support_ticket_list, name='support_ticket_list'),
    path('support/create/', views.support_ticket_create, name='support_ticket_create'),
    path('support/<int:pk>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support/<int:pk>/update-status/', views.support_ticket_update_status, name='support_ticket_update_status'),
    path('support/<int:ticket_id>/get-new-messages/', views.get_new_messages, name='get_new_messages'),
] 