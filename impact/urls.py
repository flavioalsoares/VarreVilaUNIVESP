from django.urls import path
from . import views

app_name = 'impact'

urlpatterns = [
    path('', views.lista_relatorios, name='lista'),
    path('evento/<int:event_pk>/registrar/', views.registrar_impacto, name='registrar'),
    path('evento/<int:event_pk>/editar/', views.editar_impacto, name='editar'),
]
