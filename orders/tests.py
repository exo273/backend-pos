from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from pos.models import Zone, Table
from menu.models import MenuCategory, MenuItem
from .models import Order, OrderItem, Payment


class OrderModelTest(TestCase):
    """Tests para el modelo Order"""
    
    def setUp(self):
        self.zone = Zone.objects.create(name="Test Zone", display_order=1)
        self.table = Table.objects.create(zone=self.zone, number="T1", capacity=4)
        
        self.order = Order.objects.create(
            table=self.table,
            customer_name="Juan Pérez"
        )
    
    def test_order_creation(self):
        """Test creación de orden"""
        self.assertIsNotNone(self.order.order_number)
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.customer_name, "Juan Pérez")
    
    def test_order_number_auto_generation(self):
        """Test generación automática de número de orden"""
        self.assertTrue(self.order.order_number.startswith('ORD-'))


class OrderItemModelTest(TestCase):
    """Tests para el modelo OrderItem"""
    
    def setUp(self):
        self.zone = Zone.objects.create(name="Test Zone", display_order=1)
        self.table = Table.objects.create(zone=self.zone, number="T1", capacity=4)
        self.order = Order.objects.create(table=self.table)
        
        self.category = MenuCategory.objects.create(name="Test", display_order=1)
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name="Test Item",
            price=Decimal('10000')
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.menu_item,
            quantity=2
        )
    
    def test_order_item_creation(self):
        """Test creación de item de orden"""
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, Decimal('10000'))
    
    def test_subtotal_calculation(self):
        """Test cálculo automático de subtotal"""
        self.assertEqual(self.order_item.subtotal, Decimal('20000'))
    
    def test_order_total_recalculation(self):
        """Test que la orden recalcula su total"""
        self.order.refresh_from_db()
        self.assertGreater(self.order.total, Decimal('0'))


class PaymentModelTest(TestCase):
    """Tests para el modelo Payment"""
    
    def setUp(self):
        self.zone = Zone.objects.create(name="Test Zone", display_order=1)
        self.table = Table.objects.create(zone=self.zone, number="T1", capacity=4)
        self.order = Order.objects.create(
            table=self.table,
            total=Decimal('20000')
        )
    
    def test_payment_creation(self):
        """Test creación de pago"""
        payment = Payment.objects.create(
            order=self.order,
            payment_method='cash',
            amount=Decimal('20000'),
            status='completed'
        )
        
        self.assertEqual(payment.payment_method, 'cash')
        self.assertEqual(payment.amount, Decimal('20000'))
        self.assertTrue(self.order.is_fully_paid)


class OrderAPITest(TestCase):
    """Tests para la API de Orders"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.zone = Zone.objects.create(name="Test Zone", display_order=1)
        self.table = Table.objects.create(zone=self.zone, number="T1", capacity=4)
        self.category = MenuCategory.objects.create(name="Test", display_order=1)
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name="Test Item",
            price=Decimal('10000')
        )
    
    def test_list_orders(self):
        """Test listar órdenes"""
        Order.objects.create(table=self.table)
        response = self.client.get('/api/orders/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_order(self):
        """Test crear orden con items"""
        data = {
            'table': self.table.id,
            'customer_name': 'Test Customer',
            'items': [
                {
                    'menu_item': self.menu_item.id,
                    'quantity': 2,
                    'notes': 'Sin cebolla'
                }
            ]
        }
        response = self.client.post('/api/orders/orders/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        
        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertGreater(order.total, Decimal('0'))
    
    def test_add_payment_to_order(self):
        """Test agregar pago a orden"""
        order = Order.objects.create(table=self.table, total=Decimal('20000'))
        
        data = {
            'payment_method': 'cash',
            'amount': '20000'
        }
        response = self.client.post(f'/api/orders/orders/{order.id}/add_payment/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(order.payments.count(), 1)
    
    def test_change_order_status(self):
        """Test cambiar estado de orden"""
        order = Order.objects.create(table=self.table)
        
        data = {'status': 'preparing'}
        response = self.client.post(f'/api/orders/orders/{order.id}/change_status/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'preparing')
