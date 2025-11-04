from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import MirroredProduct, MirroredRecipe


class MirroredProductModelTest(TestCase):
    """Tests para el modelo MirroredProduct"""
    
    def setUp(self):
        self.product = MirroredProduct.objects.create(
            original_id=1,
            name="Carne de Res",
            sku="CARNE-001",
            unit_cost=Decimal('8000'),
            current_stock=Decimal('50.500'),
            unit_of_measure='kg'
        )
    
    def test_product_creation(self):
        """Test creación de producto espejo"""
        self.assertEqual(self.product.original_id, 1)
        self.assertEqual(self.product.name, "Carne de Res")
        self.assertEqual(self.product.unit_cost, Decimal('8000'))
        self.assertTrue(self.product.is_active)
    
    def test_product_str(self):
        """Test representación en string"""
        expected = "Carne de Res (ID: 1) - $8000"
        self.assertEqual(str(self.product), expected)


class MirroredRecipeModelTest(TestCase):
    """Tests para el modelo MirroredRecipe"""
    
    def setUp(self):
        self.recipe = MirroredRecipe.objects.create(
            original_id=1,
            name="Salsa Criolla",
            production_cost=Decimal('3000'),
            yield_quantity=Decimal('4'),
            yield_unit='porción'
        )
    
    def test_recipe_creation(self):
        """Test creación de receta espejo"""
        self.assertEqual(self.recipe.original_id, 1)
        self.assertEqual(self.recipe.name, "Salsa Criolla")
        self.assertTrue(self.recipe.is_active)
    
    def test_cost_per_unit_calculation(self):
        """Test cálculo de costo por unidad"""
        self.recipe.calculate_cost_per_unit()
        
        # 3000 / 4 = 750
        self.assertEqual(self.recipe.cost_per_unit, Decimal('750'))


class MirroredProductAPITest(TestCase):
    """Tests para la API de MirroredProduct"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.product = MirroredProduct.objects.create(
            original_id=1,
            name="Test Product",
            unit_cost=Decimal('5000'),
            current_stock=Decimal('100')
        )
    
    def test_list_products(self):
        """Test listar productos espejo"""
        response = self.client.get('/api/catalog/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_retrieve_product(self):
        """Test obtener detalle de producto espejo"""
        response = self.client.get(f'/api/catalog/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Product')


class MirroredRecipeAPITest(TestCase):
    """Tests para la API de MirroredRecipe"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.recipe = MirroredRecipe.objects.create(
            original_id=1,
            name="Test Recipe",
            production_cost=Decimal('4000'),
            yield_quantity=Decimal('2')
        )
        self.recipe.calculate_cost_per_unit()
    
    def test_list_recipes(self):
        """Test listar recetas espejo"""
        response = self.client.get('/api/catalog/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_retrieve_recipe(self):
        """Test obtener detalle de receta espejo"""
        response = self.client.get(f'/api/catalog/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Recipe')
        self.assertEqual(Decimal(response.data['cost_per_unit']), Decimal('2000'))
