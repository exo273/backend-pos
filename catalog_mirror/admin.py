from django.contrib import admin
from .models import MirroredProduct, MirroredRecipe


@admin.register(MirroredProduct)
class MirroredProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'original_id', 'sku', 'unit_cost', 'current_stock', 
                    'unit_of_measure', 'is_active', 'last_synced_at']
    list_filter = ['is_active', 'last_synced_at', 'created_at']
    search_fields = ['name', 'sku', 'original_id']
    ordering = ['name']
    readonly_fields = ['original_id', 'last_synced_at', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('original_id', 'name', 'sku', 'unit_of_measure')
        }),
        ('Costos y Stock', {
            'fields': ('unit_cost', 'current_stock')
        }),
        ('Estado', {
            'fields': ('is_active', 'last_synced_at', 'created_at')
        }),
    )


@admin.register(MirroredRecipe)
class MirroredRecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'original_id', 'production_cost', 'yield_quantity', 
                    'yield_unit', 'cost_per_unit', 'is_active', 'last_synced_at']
    list_filter = ['is_active', 'last_synced_at', 'created_at']
    search_fields = ['name', 'original_id']
    ordering = ['name']
    readonly_fields = ['original_id', 'cost_per_unit', 'last_synced_at', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('original_id', 'name')
        }),
        ('Costos', {
            'fields': ('production_cost', 'yield_quantity', 'yield_unit', 'cost_per_unit')
        }),
        ('Estado', {
            'fields': ('is_active', 'last_synced_at', 'created_at')
        }),
    )
