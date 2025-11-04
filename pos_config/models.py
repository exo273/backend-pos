"""
Modelos para configuración del POS
"""
from django.db import models


class PaymentMethod(models.Model):
    """
    Modelo para métodos de pago del POS
    Ejemplo: Efectivo, Tarjeta, Junaeb, Amipass, etc.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre del método de pago'
    )
    logo = models.ImageField(
        upload_to='payment_logos/',
        null=True,
        blank=True,
        verbose_name='Logo',
        help_text='Logo o icono del método de pago'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo aparecerá en el POS'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción opcional del método de pago'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = 'Método de Pago'
        verbose_name_plural = 'Métodos de Pago'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Printer(models.Model):
    """
    Modelo para impresoras configuradas
    Soporta impresoras fiscales y térmicas
    """
    TYPE_CHOICES = [
        ('fiscal', 'Fiscal'),
        ('thermal', 'Térmica'),
    ]
    
    CONNECTION_CHOICES = [
        ('usb', 'USB'),
        ('network', 'Red (IP)'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre de la impresora (ej. "Caja 1")'
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name='Tipo',
        help_text='Tipo de impresora'
    )
    connection_type = models.CharField(
        max_length=50,
        choices=CONNECTION_CHOICES,
        verbose_name='Conexión',
        help_text='Tipo de conexión'
    )
    ip_address = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='Dirección IP para impresoras de red'
    )
    port = models.IntegerField(
        null=True,
        blank=True,
        default=9100,
        verbose_name='Puerto',
        help_text='Puerto de red (por defecto 9100 para impresoras térmicas)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Si está activa se puede usar en el POS'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Notas sobre la configuración de la impresora'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    
    class Meta:
        db_table = 'printers'
        verbose_name = 'Impresora'
        verbose_name_plural = 'Impresoras'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
