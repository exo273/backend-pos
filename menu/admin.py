from django.contrib import admin
from .models import MenuCategory, MenuItem, MenuItemComponent


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    list_editable = ['display_order', 'is_active']


class MenuItemComponentInline(admin.TabularInline):
    model = MenuItemComponent
    extra = 1
    fields = ['component_type', 'product_id', 'recipe_id', 'quantity', 'cached_unit_cost']
    readonly_fields = ['cached_unit_cost']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'cached_cost', 'profit_margin_display', 
                    'is_available', 'display_order', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['category__display_order', 'display_order', 'name']
    list_editable = ['is_available', 'display_order']
    readonly_fields = ['cached_cost', 'profit_margin_display']
    inlines = [MenuItemComponentInline]
    
    def profit_margin_display(self, obj):
        return f"{obj.profit_margin:.2f}%"
    profit_margin_display.short_description = 'Margen'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


@admin.register(MenuItemComponent)
class MenuItemComponentAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'component_type', 'product_id', 'recipe_id', 
                    'quantity', 'cached_unit_cost', 'total_cost_display']
    list_filter = ['component_type', 'menu_item__category']
    search_fields = ['menu_item__name']
    readonly_fields = ['cached_unit_cost']
    
    def total_cost_display(self, obj):
        return f"${obj.get_cost():.2f}"
    total_cost_display.short_description = 'Costo Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('menu_item', 'menu_item__category')
