from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('forgeapp.urls')),
    path('finance/', include('finance.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # Añadimos las URLs de autenticación
    path('checkout/', include('checkout_counters.urls')),
    path('pdf/', include('pdf_generator.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
