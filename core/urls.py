from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('forgeapp.urls')),
    path('finance/', include('finance.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('checkout/', include('checkout_counters.urls')),
    path('pdf/', include('pdf_generator.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
