from django.contrib import admin
from .models import Zone, Table


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'zone', 'capacity', 'status', 'is_active', 'created_at']
    list_filter = ['zone', 'status', 'is_active', 'created_at']
    search_fields = ['number']
    ordering = ['zone__name', 'number']
    list_editable = ['status', 'is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('zone')
