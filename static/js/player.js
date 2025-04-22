// Инициализация переменных плеера
let audioPlayer = document.getElementById('audioPlayer');
let player = document.getElementById('player');
let playPauseButton = document.getElementById('playPauseButton');
let playPauseIcon = document.getElementById('playPauseIcon');
let progressBar = document.querySelector('.progress-bar');
let progress = document.getElementById('progressBar');
let currentTimeSpan = document.getElementById('currentTime');
let durationSpan = document.getElementById('duration');
let volumeSlider = document.getElementById('volumeSlider');
let volumeButton = document.getElementById('volumeButton');
let volumeIcon = document.getElementById('volumeIcon');
let currentTrackId = null;
let wasPlaying = false;
let isShuffleEnabled = false;
let repeatMode = 'none'; // 'none', 'all', 'one'
let playlist = [];

// Форматирование времени
function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const minutes = Math.floor(seconds / 60);
    seconds = Math.floor(seconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Обновление прогресс-бара
function updateProgress() {
    if (audioPlayer.duration) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        document.querySelector('.progress-bar').style.width = `${progress}%`;
        document.getElementById('currentTime').textContent = formatTime(audioPlayer.currentTime);
        document.getElementById('duration').textContent = formatTime(audioPlayer.duration);
    }
}

// Управление воспроизведением
function togglePlay() {
    if (audioPlayer.paused) {
        audioPlayer.play().then(() => {
            updatePlayPauseIcon(true);
            const currentTrackButton = document.querySelector(`[data-track-id="${currentTrackId}"] .play-button i`);
            if (currentTrackButton) {
                currentTrackButton.className = 'fas fa-pause';
            }
        });
    } else {
        audioPlayer.pause();
        updatePlayPauseIcon(false);
        const currentTrackButton = document.querySelector(`[data-track-id="${currentTrackId}"] .play-button i`);
        if (currentTrackButton) {
            currentTrackButton.className = 'fas fa-play';
        }
    }
}

function updatePlayPauseIcon(isPlaying) {
    playPauseIcon.className = isPlaying ? 'fas fa-pause fa-lg' : 'fas fa-play fa-lg';
}

// Управление громкостью
function updateVolumeIcon(volume) {
    if (volume === 0) {
        volumeIcon.className = 'fas fa-volume-mute';
    } else if (volume < 0.5) {
        volumeIcon.className = 'fas fa-volume-down';
    } else {
        volumeIcon.className = 'fas fa-volume-up';
    }
}

function toggleMute() {
    if (audioPlayer.volume > 0) {
        audioPlayer.dataset.previousVolume = audioPlayer.volume;
        audioPlayer.volume = 0;
        volumeSlider.value = 0;
    } else {
        audioPlayer.volume = audioPlayer.dataset.previousVolume || 1;
        volumeSlider.value = audioPlayer.volume * 100;
    }
    updateVolumeIcon(audioPlayer.volume);
}

// Управление перемоткой
let isDragging = false;

progress.addEventListener('mousedown', function(e) {
    isDragging = true;
    progress.classList.add('dragging');
    wasPlaying = !audioPlayer.paused;
    if (wasPlaying) audioPlayer.pause();
    updateProgressFromMouse(e);
});

document.addEventListener('mousemove', function(e) {
    if (isDragging) {
        updateProgressFromMouse(e);
    }
});

document.addEventListener('mouseup', function() {
    if (isDragging) {
        isDragging = false;
        progress.classList.remove('dragging');
        if (wasPlaying) audioPlayer.play();
    }
});

function updateProgressFromMouse(e) {
    const rect = progress.getBoundingClientRect();
    const pos = Math.min(Math.max(0, e.clientX - rect.left), rect.width) / rect.width;
    if (audioPlayer.duration) {
        audioPlayer.currentTime = pos * audioPlayer.duration;
        updateProgress();
    }
}

// Инициализация плеера
document.addEventListener('DOMContentLoaded', () => {
    // Добавляем обработчики событий
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('loadedmetadata', updateProgress);
    
    progress.addEventListener('click', function(e) {
        const rect = progress.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        if (audioPlayer.duration) {
            audioPlayer.currentTime = pos * audioPlayer.duration;
            updateProgress();
        }
    });
    
    volumeSlider.addEventListener('input', (e) => {
        const volume = e.target.value / 100;
        audioPlayer.volume = volume;
        updateVolumeIcon(volume);
    });
    
    // Инициализация громкости
    audioPlayer.volume = volumeSlider.value / 100;
    
    // Добавляем обработчики для кнопок управления
    document.getElementById('shuffleButton').addEventListener('click', toggleShuffle);
    document.getElementById('repeatButton').addEventListener('click', toggleRepeat);
});

// Функции управления плейлистом
function toggleShuffle() {
    isShuffleEnabled = !isShuffleEnabled;
    const shuffleButton = document.getElementById('shuffleButton');
    shuffleButton.classList.toggle('active');
}

function toggleRepeat() {
    const repeatButton = document.getElementById('repeatButton');
    switch (repeatMode) {
        case 'none':
            repeatMode = 'one';
            repeatButton.classList.add('active');
            repeatButton.innerHTML = '<i class="fas fa-redo-alt"></i>';
            break;
        case 'one':
            repeatMode = 'all';
            repeatButton.classList.add('active');
            repeatButton.innerHTML = '<i class="fas fa-redo-alt"></i><span class="position-absolute" style="font-size: 0.7em;">A</span>';
            break;
        case 'all':
            repeatMode = 'none';
            repeatButton.classList.remove('active');
            repeatButton.innerHTML = '<i class="fas fa-redo-alt"></i>';
            break;
    }
}

const prevButton = document.getElementById('prevButton');
const nextButton = document.getElementById('nextButton');
const repeatButton = document.getElementById('repeatButton');

function previousTrack() {
    const tracks = document.querySelectorAll('[data-track-id]');
    const currentIndex = Array.from(tracks).findIndex(track => track.dataset.trackId === currentTrackId);
    if (currentIndex > 0) {
        playTrack(tracks[currentIndex - 1].dataset.trackId);
    }
}

function nextTrack() {
    const tracks = document.querySelectorAll('[data-track-id]');
    const currentIndex = Array.from(tracks).findIndex(track => track.dataset.trackId === currentTrackId);
    if (currentIndex < tracks.length - 1) {
        playTrack(tracks[currentIndex + 1].dataset.trackId);
    } else if (isRepeatEnabled) {
        playTrack(tracks[0].dataset.trackId);
    }
}

function playTrack(trackId) {
    // Implementation of playTrack function
}

let isRepeatEnabled = false;

function toggleRepeat() {
    isRepeatEnabled = !isRepeatEnabled;
    repeatButton.classList.toggle('active');
}

audioPlayer.addEventListener('ended', () => {
    if (isRepeatEnabled) {
        audioPlayer.currentTime = 0;
        audioPlayer.play();
    } else {
        nextTrack();
    }
});

function setProgress(e) {
    const width = progressContainer.clientWidth;
    const clickX = e.offsetX;
    const duration = audioPlayer.duration;
    audioPlayer.currentTime = (clickX / width) * duration;
}

const progressContainer = document.querySelector('.progress-container');
progressContainer.addEventListener('click', setProgress);
progressContainer.addEventListener('mousedown', () => {
    progressContainer.addEventListener('mousemove', setProgress);
    progressContainer.addEventListener('mouseup', () => {
        progressContainer.removeEventListener('mousemove', setProgress);
        progressContainer.removeEventListener('mouseup', () => {});
    }, { once: true });
}); 