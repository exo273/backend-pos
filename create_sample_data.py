"""
Script para crear datos de ejemplo en el sistema POS.
Ejecutar: docker-compose exec django python create_sample_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders_service.settings')
django.setup()

from decimal import Decimal
from pos.models import Zone, Table
from menu.models import MenuCategory, MenuItem
from catalog_mirror.models import MirroredProduct, MirroredRecipe


def create_sample_data():
    print("🚀 Creando datos de ejemplo...")
    
    # Zonas y Mesas
    print("\n📍 Creando zonas y mesas...")
    terraza = Zone.objects.get_or_create(
        name="Terraza",
        defaults={
            'description': 'Zona al aire libre',
            'display_order': 1
        }
    )[0]
    
    salon = Zone.objects.get_or_create(
        name="Salón Principal",
        defaults={
            'description': 'Área interior principal',
            'display_order': 2
        }
    )[0]
    
    # Crear mesas para Terraza
    for i in range(1, 6):
        Table.objects.get_or_create(
            zone=terraza,
            number=f"T{i}",
            defaults={'capacity': 4}
        )
    
    # Crear mesas para Salón
    for i in range(1, 11):
        Table.objects.get_or_create(
            zone=salon,
            number=f"M{i}",
            defaults={'capacity': 4 if i <= 6 else 6}
        )
    
    print(f"✅ Creadas {Zone.objects.count()} zonas y {Table.objects.count()} mesas")
    
    # Productos y Recetas Espejo (simulados)
    print("\n📦 Creando productos y recetas espejo...")
    
    # Productos
    carne = MirroredProduct.objects.get_or_create(
        original_id=1,
        defaults={
            'name': 'Carne de Res',
            'sku': 'CARNE-001',
            'unit_cost': Decimal('8000'),
            'current_stock': Decimal('50'),
            'unit_of_measure': 'kg'
        }
    )[0]
    
    pollo = MirroredProduct.objects.get_or_create(
        original_id=2,
        defaults={
            'name': 'Pollo',
            'sku': 'POLLO-001',
            'unit_cost': Decimal('4000'),
            'current_stock': Decimal('30'),
            'unit_of_measure': 'kg'
        }
    )[0]
    
    papas = MirroredProduct.objects.get_or_create(
        original_id=3,
        defaults={
            'name': 'Papas',
            'sku': 'PAPA-001',
            'unit_cost': Decimal('800'),
            'current_stock': Decimal('100'),
            'unit_of_measure': 'kg'
        }
    )[0]
    
    # Recetas
    salsa_criolla = MirroredRecipe.objects.get_or_create(
        original_id=1,
        defaults={
            'name': 'Salsa Criolla',
            'production_cost': Decimal('2000'),
            'yield_quantity': Decimal('4'),
            'yield_unit': 'porción'
        }
    )[0]
    salsa_criolla.calculate_cost_per_unit()
    
    print(f"✅ Creados {MirroredProduct.objects.count()} productos y {MirroredRecipe.objects.count()} recetas espejo")
    
    # Categorías del Menú
    print("\n🍽️ Creando categorías del menú...")
    
    entradas = MenuCategory.objects.get_or_create(
        name="Entradas",
        defaults={
            'description': 'Para comenzar',
            'display_order': 1
        }
    )[0]
    
    platos_fuertes = MenuCategory.objects.get_or_create(
        name="Platos Fuertes",
        defaults={
            'description': 'Platos principales',
            'display_order': 2
        }
    )[0]
    
    bebidas = MenuCategory.objects.get_or_create(
        name="Bebidas",
        defaults={
            'description': 'Bebidas frías y calientes',
            'display_order': 3
        }
    )[0]
    
    postres = MenuCategory.objects.get_or_create(
        name="Postres",
        defaults={
            'description': 'Para terminar dulce',
            'display_order': 4
        }
    )[0]
    
    print(f"✅ Creadas {MenuCategory.objects.count()} categorías")
    
    # Items del Menú
    print("\n🍔 Creando items del menú...")
    
    # Entrada
    MenuItem.objects.get_or_create(
        category=entradas,
        name="Tequeños",
        defaults={
            'description': 'Tequeños de queso (6 unidades)',
            'price': Decimal('5000'),
            'cached_cost': Decimal('2000'),
            'preparation_time': 10,
            'is_available': True
        }
    )
    
    # Platos Fuertes
    lomo = MenuItem.objects.get_or_create(
        category=platos_fuertes,
        name="Lomo a la Plancha",
        defaults={
            'description': 'Lomo de res con papas fritas y ensalada',
            'price': Decimal('15000'),
            'cached_cost': Decimal('7000'),
            'preparation_time': 20,
            'is_available': True
        }
    )[0]
    
    pollo_plato = MenuItem.objects.get_or_create(
        category=platos_fuertes,
        name="Pollo Grillado",
        defaults={
            'description': 'Pechuga de pollo con papas y vegetales',
            'price': Decimal('12000'),
            'cached_cost': Decimal('5000'),
            'preparation_time': 18,
            'is_available': True
        }
    )[0]
    
    # Bebidas
    MenuItem.objects.get_or_create(
        category=bebidas,
        name="Jugo Natural",
        defaults={
            'description': 'Jugo de frutas naturales',
            'price': Decimal('3000'),
            'cached_cost': Decimal('1000'),
            'preparation_time': 5,
            'is_available': True
        }
    )
    
    MenuItem.objects.get_or_create(
        category=bebidas,
        name="Gaseosa",
        defaults={
            'description': 'Gaseosa 350ml',
            'price': Decimal('2500'),
            'cached_cost': Decimal('800'),
            'preparation_time': 2,
            'is_available': True
        }
    )
    
    # Postres
    MenuItem.objects.get_or_create(
        category=postres,
        name="Torta de Chocolate",
        defaults={
            'description': 'Porción de torta de chocolate',
            'price': Decimal('4000'),
            'cached_cost': Decimal('1500'),
            'preparation_time': 5,
            'is_available': True
        }
    )
    
    print(f"✅ Creados {MenuItem.objects.count()} items del menú")
    
    # Componentes (ejemplo)
    from menu.models import MenuItemComponent
    
    print("\n🔧 Creando componentes de ejemplo...")
    
    # Lomo: usa carne + papas + salsa
    MenuItemComponent.objects.get_or_create(
        menu_item=lomo,
        component_type='product',
        product_id=carne.original_id,
        defaults={
            'quantity': Decimal('0.300'),  # 300g
            'cached_unit_cost': carne.unit_cost
        }
    )
    
    MenuItemComponent.objects.get_or_create(
        menu_item=lomo,
        component_type='product',
        product_id=papas.original_id,
        defaults={
            'quantity': Decimal('0.200'),  # 200g
            'cached_unit_cost': papas.unit_cost
        }
    )
    
    MenuItemComponent.objects.get_or_create(
        menu_item=lomo,
        component_type='recipe',
        recipe_id=salsa_criolla.original_id,
        defaults={
            'quantity': Decimal('1'),  # 1 porción
            'cached_unit_cost': salsa_criolla.cost_per_unit
        }
    )
    
    # Recalcular costos
    lomo.calculate_cost()
    pollo_plato.calculate_cost()
    
    print(f"✅ Creados componentes de ejemplo")
    
    print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
    print("\n📊 Resumen:")
    print(f"   - Zonas: {Zone.objects.count()}")
    print(f"   - Mesas: {Table.objects.count()}")
    print(f"   - Categorías: {MenuCategory.objects.count()}")
    print(f"   - Items de Menú: {MenuItem.objects.count()}")
    print(f"   - Productos Espejo: {MirroredProduct.objects.count()}")
    print(f"   - Recetas Espejo: {MirroredRecipe.objects.count()}")
    print("\n✨ Ahora puedes iniciar sesión en /admin/ y explorar el sistema")


if __name__ == '__main__':
    create_sample_data()
