from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, resolve
import re

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Если пользователь уже авторизован, пропускаем его
        if request.user.is_authenticated:
            # Если пользователь пытается зайти на страницу входа или регистрации
            if request.path_info in [reverse('music:login'), reverse('music:register')]:
                return redirect('music:home')
            return self.get_response(request)

        # Проверяем, не является ли путь исключением
        path = request.path_info.lstrip('/')
        
        # Разрешаем доступ к статическим файлам и медиа
        if path.startswith(('static/', 'media/')):
            return self.get_response(request)
            
        # Разрешаем доступ к страницам входа и регистрации
        if path in ['login/', 'register/'] or path == '':
            return self.get_response(request)
            
        # Для всех остальных страниц требуем авторизацию
        return redirect('music:login') 