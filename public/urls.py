from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.sobre, name='sobre'),
    path('acoes/', views.acoes, name='acoes'),
    path('contato/', views.contato, name='contato'),
]
