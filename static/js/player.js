const audioPlayer = document.getElementById('audioPlayer');
const playPauseButton = document.getElementById('playPauseButton');
const playPauseIcon = document.getElementById('playPauseIcon');
const prevButton = document.getElementById('prevButton');
const nextButton = document.getElementById('nextButton');
const repeatButton = document.getElementById('repeatButton');
const volumeButton = document.getElementById('volumeButton');
const volumeIcon = document.getElementById('volumeIcon');
const volumeRange = document.getElementById('volumeRange');
const progressBar = document.getElementById('progressBar');
const currentTimeDisplay = document.getElementById('currentTime');
const durationDisplay = document.getElementById('duration');

let currentTrackId = null;
let isRepeatEnabled = false;

// Функции управления воспроизведением
function togglePlay() {
    if (audioPlayer.paused) {
        audioPlayer.play();
        playPauseIcon.classList.replace('fa-play', 'fa-pause');
    } else {
        audioPlayer.pause();
        playPauseIcon.classList.replace('fa-pause', 'fa-play');
    }
}

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

function toggleRepeat() {
    isRepeatEnabled = !isRepeatEnabled;
    repeatButton.classList.toggle('active');
}

// Функции управления громкостью
function toggleMute() {
    audioPlayer.muted = !audioPlayer.muted;
    updateVolumeIcon();
    volumeRange.value = audioPlayer.muted ? 0 : audioPlayer.volume * 100;
}

function updateVolumeIcon() {
    const volume = audioPlayer.volume;
    const isMuted = audioPlayer.muted;
    
    if (isMuted || volume === 0) {
        volumeIcon.className = 'fas fa-volume-mute';
    } else if (volume < 0.5) {
        volumeIcon.className = 'fas fa-volume-down';
    } else {
        volumeIcon.className = 'fas fa-volume-up';
    }
}

// Функции обновления прогресса
function updateProgress() {
    if (!audioPlayer.duration) return;
    
    const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progressBar.style.width = `${progress}%`;
    currentTimeDisplay.textContent = formatTime(audioPlayer.currentTime);
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Обработчики событий
playPauseButton.addEventListener('click', togglePlay);
prevButton.addEventListener('click', previousTrack);
nextButton.addEventListener('click', nextTrack);
repeatButton.addEventListener('click', toggleRepeat);
volumeButton.addEventListener('click', toggleMute);

volumeRange.addEventListener('input', (e) => {
    audioPlayer.volume = e.target.value / 100;
    audioPlayer.muted = false;
    updateVolumeIcon();
});

audioPlayer.addEventListener('timeupdate', updateProgress);
audioPlayer.addEventListener('loadedmetadata', () => {
    durationDisplay.textContent = formatTime(audioPlayer.duration);
});

audioPlayer.addEventListener('ended', () => {
    if (isRepeatEnabled) {
        audioPlayer.currentTime = 0;
        audioPlayer.play();
    } else {
        nextTrack();
    }
}); 