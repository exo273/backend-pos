from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class Order(models.Model):
    """Orden de un cliente (puede ser para mesa o para llevar)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('preparing', 'En Preparación'),
        ('ready', 'Listo'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Relación con mesa (opcional para órdenes para llevar)
    table = models.ForeignKey('pos.Table', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Información del cliente (opcional)
    customer_name = models.CharField(max_length=150, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Notas especiales
    notes = models.TextField(blank=True)
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Control de tiempos
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)  # Cuando pasa a "preparing"
    completed_at = models.DateTimeField(null=True, blank=True)  # Cuando pasa a "delivered"
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['table', 'status']),
        ]

    def __str__(self):
        return f"Orden {self.order_number} - {self.get_status_display()}"

    def calculate_total(self):
        """Calcula los totales de la orden"""
        items_total = sum(item.subtotal for item in self.items.all())
        self.subtotal = items_total
        self.tax = items_total * Decimal('0.19')  # IVA 19% en Chile
        self.total = self.subtotal + self.tax
        self.save(update_fields=['subtotal', 'tax', 'total'])

    @property
    def is_fully_paid(self):
        """Verifica si la orden está completamente pagada"""
        total_paid = sum(payment.amount for payment in self.payments.filter(status='completed'))
        return total_paid >= self.total

    def broadcast_to_kds(self):
        """Envía la orden a la pantalla KDS (Kitchen Display System) vía WebSocket"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'kds',
            {
                'type': 'order_update',
                'order_id': self.id,
                'order_number': self.order_number,
                'status': self.status,
                'items': [
                    {
                        'id': item.id,
                        'menu_item_name': item.menu_item.name,
                        'quantity': str(item.quantity),
                        'notes': item.notes,
                    }
                    for item in self.items.all()
                ],
                'table': self.table.number if self.table else None,
                'created_at': self.created_at.isoformat(),
            }
        )

    def save(self, *args, **kwargs):
        # Auto-generar número de orden
        if not self.order_number:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.order_number = f"ORD-{timestamp}"
        
        # Registrar tiempos según cambio de estado
        if self.pk:
            old_instance = Order.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if self.status == 'preparing' and not self.started_at:
                    self.started_at = timezone.now()
                elif self.status == 'delivered' and not self.completed_at:
                    self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Broadcast a KDS cuando cambia el estado
        if self.status in ['pending', 'preparing', 'ready']:
            self.broadcast_to_kds()


class OrderItem(models.Model):
    """Items individuales de una orden"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.PROTECT)
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Notas especiales para este item (ej: "sin cebolla", "punto medio")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} - Orden {self.order.order_number}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.unit_price = self.menu_item.price
        self.subtotal = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
        
        # Recalcular total de la orden
        self.order.calculate_total()


class Payment(models.Model):
    """Pagos asociados a una orden (puede haber múltiples pagos para una orden)"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('convenio', 'Convenio'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Para convenios
    convenio_code = models.CharField(max_length=50, blank=True)
    convenio_name = models.CharField(max_length=150, blank=True)
    
    # Referencia de transacción (para tarjetas/transferencias)
    transaction_reference = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pago {self.get_payment_method_display()} - ${self.amount} - Orden {self.order.order_number}"

    def check_order_fully_paid(self):
        """Verifica si la orden está completamente pagada y publica evento"""
        if self.order.is_fully_paid:
            # Publicar evento al microservicio de operaciones para descontar stock
            from .tasks import publish_order_paid
            publish_order_paid.delay(self.order.id)

    def save(self, *args, **kwargs):
        # Validar convenio
        if self.payment_method == 'convenio' and not self.convenio_code:
            raise ValueError("convenio_code es requerido para pagos con convenio")
        
        # Registrar tiempo de completado
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Verificar si la orden está completamente pagada
        if self.status == 'completed':
            self.check_order_fully_paid()
