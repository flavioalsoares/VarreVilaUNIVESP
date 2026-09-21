from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

roteador = DefaultRouter()
roteador.register('eventos', views.EventoViewSet, basename='evento')

urlpatterns = [
    path('impacto/resumo/', views.ResumoView.as_view(), name='resumo'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='docs'),
]
urlpatterns += roteador.urls
