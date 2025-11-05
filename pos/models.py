"""
Modelos de la aplicación POS.
Gestiona zonas y mesas del restaurante.
"""

from django.db import models
from django.core.validators import MinValueValidator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Zone(models.Model):
    """Zona del restaurante."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['name']

    def __str__(self):
        return self.name


class Table(models.Model):
    """Mesa del restaurante."""
    
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('occupied', 'Ocupada'),
        ('reserved', 'Reservada'),
    ]
    
    zone = models.ForeignKey(
        Zone,
        on_delete=models.PROTECT,
        related_name='tables',
        verbose_name="Zona"
    )
    number = models.CharField(max_length=20, verbose_name="Número")
    capacity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Capacidad",
        help_text="Número de comensales"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name="Estado"
    )
    position_x = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Posición X",
        help_text="Para el editor visual"
    )
    position_y = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Posición Y",
        help_text="Para el editor visual"
    )
    width = models.IntegerField(
        default=1,
        verbose_name="Ancho",
        help_text="Ancho en celdas de cuadrícula"
    )
    height = models.IntegerField(
        default=1,
        verbose_name="Alto",
        help_text="Alto en celdas de cuadrícula"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['zone', 'number']
        unique_together = [['zone', 'number']]
        indexes = [
            models.Index(fields=['zone', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Mesa {self.number} - {self.zone.name}"

    def occupy(self):
        """Marca la mesa como ocupada."""
        self.status = 'occupied'
        self.save()
        self.broadcast_status_change()

    def release(self):
        """Libera la mesa."""
        self.status = 'available'
        self.save()
        self.broadcast_status_change()

    def reserve(self):
        """Reserva la mesa."""
        self.status = 'reserved'
        self.save()
        self.broadcast_status_change()

    def broadcast_status_change(self):
        """Envía actualización del estado de la mesa via WebSocket."""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'tables_status',
            {
                'type': 'table_status_update',
                'table_id': self.id,
                'table_number': self.number,
                'zone_name': self.zone.name,
                'status': self.status,
            }
        )

    @property
    def current_order(self):
        """Obtiene la orden activa en esta mesa."""
        return self.orders.filter(status='open').first()

    @property
    def is_available(self):
        """Verifica si la mesa está disponible."""
        return self.status == 'available'

    def save(self, *args, **kwargs):
        """Al guardar, validar el estado."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Si no es nueva y cambió el estado, broadcast
        if not is_new:
            self.broadcast_status_change()
