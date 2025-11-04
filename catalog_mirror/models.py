from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class MirroredProduct(models.Model):
    """Copia local de productos del microservicio de operaciones"""
    
    # ID original del microservicio de operaciones
    original_id = models.IntegerField(unique=True, db_index=True)
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    
    # Costo unitario actual (se actualiza mediante eventos)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Stock actual (se actualiza mediante eventos)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Unidad de medida
    unit_of_measure = models.CharField(max_length=50, default='unidad')
    
    # Metadata
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['original_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} (ID: {self.original_id}) - ${self.unit_cost}"


class MirroredRecipe(models.Model):
    """Copia local de recetas del microservicio de operaciones"""
    
    # ID original del microservicio de operaciones
    original_id = models.IntegerField(unique=True, db_index=True)
    
    name = models.CharField(max_length=200)
    
    # Costo de producción (se actualiza mediante eventos)
    production_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Rendimiento de la receta
    yield_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    yield_unit = models.CharField(max_length=50, default='porción')
    
    # Costo por unidad de rendimiento
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['original_id', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} (ID: {self.original_id}) - ${self.cost_per_unit}/unidad"

    def calculate_cost_per_unit(self):
        """Calcula el costo por unidad de rendimiento"""
        if self.yield_quantity > 0:
            self.cost_per_unit = self.production_cost / self.yield_quantity
        else:
            self.cost_per_unit = Decimal('0')
        self.save(update_fields=['cost_per_unit'])
