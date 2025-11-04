from django.contrib import admin
from .models import PaymentMethod, Printer


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'connection_type', 'ip_address', 'is_active']
    list_filter = ['type', 'connection_type', 'is_active']
    search_fields = ['name', 'ip_address']
