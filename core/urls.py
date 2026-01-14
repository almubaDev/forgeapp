from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from pdf_generator.views import verificar_comprobante

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('forgeapp.urls')),
    path('finance/', include('finance.urls')),
    path('payments/', include('payments.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/', template_name='registration/logged_out.html', http_method_names=['get', 'post']), name='logout'),
    path('pdf/', include('pdf_generator.urls')),
    # Ruta directa para verificación de comprobantes
    path('comprobante/verificar/<str:receipt_number>/<str:verification_code>/', verificar_comprobante, name='verificar_comprobante')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
