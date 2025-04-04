from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Track, Playlist, UserProfile

class TrackUploadForm(forms.ModelForm):
    """Форма для загрузки трека"""
    class Meta:
        model = Track
        fields = ['title', 'artist', 'album', 'audio_file', 'cover']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название трека'
            }),
            'artist': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя исполнителя'
            }),
            'album': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название альбома (необязательно)'
            }),
            'audio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'audio/mp3,audio/wav'
            }),
            'cover': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'title': 'Название трека',
            'artist': 'Исполнитель',
            'album': 'Альбом',
            'audio_file': 'Аудиофайл (MP3 или WAV)',
            'cover': 'Обложка (изображение)'
        }
        help_texts = {
            'audio_file': 'Поддерживаются форматы MP3 и WAV',
            'cover': 'Рекомендуемый размер: 300x300 пикселей'
        }

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        if audio_file:
            if not audio_file.name.lower().endswith(('.mp3', '.wav')):
                raise forms.ValidationError('Поддерживаются только файлы MP3 и WAV')
            if audio_file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Размер файла не должен превышать 10MB')
        return audio_file

    def clean_cover(self):
        cover = self.cleaned_data.get('cover')
        if cover:
            if not cover.content_type.startswith('image/'):
                raise forms.ValidationError('Загрузите изображение')
            if cover.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Размер изображения не должен превышать 5MB')
        return cover

class PlaylistForm(forms.ModelForm):
    """Форма для создания и редактирования плейлиста"""
    class Meta:
        model = Playlist
        fields = ['name', 'description', 'cover']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=UserProfile.ROLES,
        required=True,
        label='Роль',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Создаем профиль пользователя с выбранной ролью
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        
        return user 