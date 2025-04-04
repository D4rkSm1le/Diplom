# Disgen Music - Личный музыкальный сервис

Этот проект представляет собой веб-приложение для управления личной музыкальной коллекцией с возможностью интеграции с Disgen Music API.

## Основные функции

- Загрузка и управление музыкальными треками
- Создание и управление плейлистами
- Поиск и добавление треков из Disgen Music
- Воспроизведение музыки
- Управление обложками альбомов

## Требования

- Python 3.8+
- Django 4.2+
- Pillow
- requests
- django-crispy-forms
- crispy-bootstrap5

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/disgen-music.git
cd disgen-music
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории проекта и добавьте в него:
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DISGEN_MUSIC_TOKEN=your-disgen-music-token
```

5. Примените миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

## Использование

1. Откройте браузер и перейдите по адресу `http://localhost:8000`
2. Зарегистрируйтесь или войдите в систему
3. Начните добавлять треки и создавать плейлисты


```

## Лицензия

MIT License 
