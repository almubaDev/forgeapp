# forgeapp/admin.py
from django.contrib import admin
from .models import Application, Client, Subscription, ApplicationConfig

class ApplicationConfigInline(admin.TabularInline):
    model = ApplicationConfig
    extra = 1
    fields = ('key', 'value', 'field_type', 'description')
    readonly_fields = ('is_encrypted',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    inlines = [ApplicationConfigInline]

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'status', 'created_at')
    search_fields = ('name', 'email', 'company')
    list_filter = ('status', 'created_at')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('client', 'application', 'status', 'price', 'start_date', 'end_date')
    search_fields = ('client__name', 'application__name')
    list_filter = ('status', 'start_date', 'end_date')
    autocomplete_fields = ['client', 'application']

@admin.register(ApplicationConfig)
class ApplicationConfigAdmin(admin.ModelAdmin):
    list_display = ('application', 'key', 'field_type', 'created_at', 'updated_at')
    list_filter = ('field_type', 'application', 'created_at')
    search_fields = ('key', 'description')
    readonly_fields = ('is_encrypted',)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.field_type == 'password' and obj.is_encrypted:
            form.base_fields['value'].initial = obj.get_value()
        return form
