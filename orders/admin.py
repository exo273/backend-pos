from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['menu_item', 'quantity', 'unit_price', 'subtotal', 'notes']
    readonly_fields = ['unit_price', 'subtotal']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ['payment_method', 'amount', 'status', 'convenio_code', 'transaction_reference']
    readonly_fields = ['completed_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table', 'status', 'customer_name', 
                    'total', 'is_fully_paid', 'created_at']
    list_filter = ['status', 'created_at', 'table__zone']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'subtotal', 'tax', 'total', 'is_fully_paid',
                       'created_at', 'started_at', 'completed_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('order_number', 'table', 'status')
        }),
        ('Cliente', {
            'fields': ('customer_name', 'customer_phone', 'notes')
        }),
        ('Totales', {
            'fields': ('subtotal', 'tax', 'total', 'is_fully_paid')
        }),
        ('Tiempos', {
            'fields': ('created_at', 'started_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('table', 'table__zone')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'subtotal', 'created_at']
    list_filter = ['created_at', 'menu_item__category']
    search_fields = ['order__order_number', 'menu_item__name']
    ordering = ['-created_at']
    readonly_fields = ['unit_price', 'subtotal', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'menu_item', 'menu_item__category'
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'amount', 'status', 
                    'convenio_code', 'created_at', 'completed_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['order__order_number', 'convenio_code', 'transaction_reference']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('order', 'payment_method', 'amount', 'status')
        }),
        ('Detalles de Pago', {
            'fields': ('convenio_code', 'convenio_name', 'transaction_reference', 'notes')
        }),
        ('Tiempos', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order')
