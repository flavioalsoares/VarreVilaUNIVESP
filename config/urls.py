from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('public.urls')),        # Área pública institucional (raiz)
    path('sistema/', include('dashboard.urls')),  # Sistema interno — dashboard
    path('users/', include('users.urls')),
    path('events/', include('events.urls')),
    path('impact/', include('impact.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
