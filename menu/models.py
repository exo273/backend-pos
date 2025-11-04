from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class MenuCategory(models.Model):
    """Categorías del menú (Entradas, Platos Fuertes, Postres, Bebidas, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Menu Categories'

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Items del menú (platos/productos que el cliente puede ordenar)"""
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name='items')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # El costo se calcula sumando los costos de todos los componentes
    cached_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    image_url = models.URLField(max_length=500, blank=True)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Tiempos de preparación (en minutos)
    preparation_time = models.IntegerField(default=15, help_text="Tiempo estimado de preparación en minutos")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.price}"

    def calculate_cost(self):
        """Calcula el costo total sumando todos los componentes"""
        total = Decimal('0')
        for component in self.components.all():
            total += component.get_cost()
        self.cached_cost = total
        self.save(update_fields=['cached_cost'])
        return total

    @property
    def profit_margin(self):
        """Calcula el margen de ganancia"""
        if self.cached_cost > 0:
            return ((self.price - self.cached_cost) / self.price) * 100
        return Decimal('0')


class MenuItemComponent(models.Model):
    """Componentes de un MenuItem (productos o recetas del microservicio de operaciones)"""
    
    COMPONENT_TYPE_CHOICES = [
        ('product', 'Producto'),
        ('recipe', 'Receta'),
    ]
    
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPE_CHOICES)
    
    # IDs que apuntan al microservicio de operaciones
    product_id = models.IntegerField(null=True, blank=True, help_text="ID del producto en el servicio de operaciones")
    recipe_id = models.IntegerField(null=True, blank=True, help_text="ID de la receta en el servicio de operaciones")
    
    quantity = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    
    # Cache local del costo unitario (se actualiza mediante eventos)
    cached_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['menu_item', 'component_type', 'product_id'],
            ['menu_item', 'component_type', 'recipe_id'],
        ]

    def __str__(self):
        if self.component_type == 'product':
            return f"{self.menu_item.name} - Product #{self.product_id} x{self.quantity}"
        return f"{self.menu_item.name} - Recipe #{self.recipe_id} x{self.quantity}"

    def get_cost(self):
        """Obtiene el costo total de este componente"""
        return self.cached_unit_cost * self.quantity

    def save(self, *args, **kwargs):
        # Validación: debe tener product_id O recipe_id, no ambos
        if self.component_type == 'product' and not self.product_id:
            raise ValueError("product_id es requerido cuando component_type es 'product'")
        if self.component_type == 'recipe' and not self.recipe_id:
            raise ValueError("recipe_id es requerido cuando component_type es 'recipe'")
        if self.product_id and self.recipe_id:
            raise ValueError("No puede tener product_id y recipe_id al mismo tiempo")
        
        super().save(*args, **kwargs)
        
        # Recalcular el costo del MenuItem padre
        self.menu_item.calculate_cost()
