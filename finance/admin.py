from django.contrib import admin
from .models import Payment, Transaction

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscription', 'amount', 'status', 'payment_date', 'due_date')
    list_filter = ('status', 'payment_date', 'due_date')
    search_fields = ('subscription__client__name', 'subscription__application__name', 'notes')
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'category', 'amount', 'date', 'description')
    list_filter = ('type', 'category', 'date')
    search_fields = ('description', 'category', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)
