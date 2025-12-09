# urls.py
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('calculate/', views.calculate, name='calculate'),  # Основной эндпоинт
    path('health/', views.health_check, name='health-check'),  # Для проверки
]