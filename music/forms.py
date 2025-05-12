from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Track, Playlist, UserProfile, Album

class TrackUploadForm(forms.ModelForm):
    """Форма для загрузки трека"""
    class Meta:
        model = Track
        fields = ['title', 'artist', 'album', 'audio_file', 'cover', 'is_explicit']
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
            'is_explicit': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'Название трека',
            'artist': 'Исполнитель',
            'album': 'Альбом',
            'audio_file': 'Аудиофайл (MP3 или WAV)',
            'cover': 'Обложка (изображение)',
            'is_explicit': 'В треке есть цензура',
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
    birth_date = forms.DateField(
        required=True,
        label='Дата рождения',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'birth_date', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Создаем профиль пользователя с выбранной ролью и датой рождения
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                birth_date=self.cleaned_data['birth_date']
            )
        
        return user

class UserUpdateForm(forms.ModelForm):
    """Форма для обновления имени пользователя"""
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите новое имя пользователя'
            })
        }
        labels = {
            'username': 'Имя пользователя'
        }

class AdminTrackForm(forms.ModelForm):
    """Форма для модерации трека администратором"""
    class Meta:
        model = Track
        fields = ['is_approved', 'moderation_comment']
        widgets = {
            'moderation_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Комментарий модератора'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'is_approved': 'Одобрен',
            'moderation_comment': 'Комментарий модератора'
        }

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'artist', 'cover', 'release_date', 'description']
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'artist': forms.TextInput(attrs={'class': 'form-control'}),
            'cover': forms.FileInput(attrs={'class': 'form-control'})
        }

class AlbumTrackForm(forms.ModelForm):
    class Meta:
        model = Track
        fields = ['title', 'audio_file', 'track_number']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'audio_file': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
            'track_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'required': True})
        }

    def clean_track_number(self):
        track_number = self.cleaned_data.get('track_number')
        album = self.instance.album if self.instance else None
        
        if album:
            # Проверяем, нет ли другого трека с таким же номером в этом альбоме
            existing_track = Track.objects.filter(
                album=album,
                track_number=track_number
            ).exclude(pk=self.instance.pk).first()
            
            if existing_track:
                raise forms.ValidationError('Трек с таким номером уже существует в этом альбоме.')
        
        return track_number

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get('audio_file')
        if not audio_file and not self.instance.pk:
            raise forms.ValidationError('Это поле обязательно для заполнения.')
        return audio_file

TrackFormSet = forms.inlineformset_factory(
    Album,
    Track,
    form=AlbumTrackForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
) 