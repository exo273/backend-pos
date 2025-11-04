from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import MenuCategory, MenuItem, MenuItemComponent


class MenuCategoryModelTest(TestCase):
    """Tests para el modelo MenuCategory"""
    
    def setUp(self):
        self.category = MenuCategory.objects.create(
            name="Entradas",
            description="Platos de entrada",
            display_order=1
        )
    
    def test_category_creation(self):
        """Test creación de categoría"""
        self.assertEqual(self.category.name, "Entradas")
        self.assertTrue(self.category.is_active)
        self.assertEqual(str(self.category), "Entradas")


class MenuItemModelTest(TestCase):
    """Tests para el modelo MenuItem"""
    
    def setUp(self):
        self.category = MenuCategory.objects.create(name="Platos Fuertes", display_order=1)
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Lomo a la Plancha",
            description="Lomo de res con papas",
            price=Decimal('15000'),
            preparation_time=20
        )
    
    def test_item_creation(self):
        """Test creación de item del menú"""
        self.assertEqual(self.item.name, "Lomo a la Plancha")
        self.assertEqual(self.item.price, Decimal('15000'))
        self.assertTrue(self.item.is_available)
    
    def test_profit_margin(self):
        """Test cálculo de margen de ganancia"""
        self.item.cached_cost = Decimal('8000')
        self.item.save()
        
        # Margen = ((15000 - 8000) / 15000) * 100 = 46.67%
        margin = self.item.profit_margin
        self.assertGreater(margin, Decimal('46'))
        self.assertLess(margin, Decimal('47'))


class MenuCategoryAPITest(TestCase):
    """Tests para la API de MenuCategory"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.category = MenuCategory.objects.create(
            name="Test Category",
            display_order=1
        )
    
    def test_list_categories(self):
        """Test listar categorías"""
        response = self.client.get('/api/menu/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_category(self):
        """Test crear categoría"""
        data = {
            'name': 'Bebidas',
            'description': 'Bebidas frías y calientes',
            'display_order': 2,
            'is_active': True
        }
        response = self.client.post('/api/menu/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuCategory.objects.count(), 2)


class MenuItemAPITest(TestCase):
    """Tests para la API de MenuItem"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.category = MenuCategory.objects.create(name="Test Category", display_order=1)
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Test Item",
            price=Decimal('10000')
        )
    
    def test_list_items(self):
        """Test listar items"""
        response = self.client.get('/api/menu/items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_item(self):
        """Test crear item"""
        data = {
            'category': self.category.id,
            'name': 'Nuevo Plato',
            'description': 'Delicioso plato',
            'price': '12000',
            'is_available': True,
            'preparation_time': 15
        }
        response = self.client.post('/api/menu/items/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuItem.objects.count(), 2)
    
    def test_recalculate_cost(self):
        """Test recalcular costo de item"""
        response = self.client.post(f'/api/menu/items/{self.item.id}/recalculate_cost/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
