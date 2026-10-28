from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.lista_eventos, name='lista'),
    path('<int:pk>/', views.detalhe_evento, name='detalhe'),
    path('novo/', views.criar_evento, name='criar'),
    path('sugerir-local/', views.sugerir_local, name='sugerir_local'),
    path('sugestoes/', views.sugestoes_de_local, name='sugestoes'),
    path('sugestoes/<int:pk>/avaliar/', views.avaliar_sugestao, name='avaliar_sugestao'),
    path('<int:pk>/editar/', views.editar_evento, name='editar'),
    path('<int:pk>/inscrever/', views.inscrever_evento, name='inscrever'),
    path('<int:pk>/cancelar/', views.cancelar_inscricao, name='cancelar'),
    path('<int:pk>/presenca/<int:user_id>/', views.confirmar_presenca, name='confirmar_presenca'),
    path('<int:pk>/presenca-publica/<int:inscricao_id>/', views.confirmar_presenca_publica,
         name='confirmar_presenca_publica'),
]
