from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Zone, Table


class ZoneModelTest(TestCase):
    """Tests para el modelo Zone"""
    
    def setUp(self):
        self.zone = Zone.objects.create(
            name="Terraza",
            description="Zona al aire libre",
            display_order=1
        )
    
    def test_zone_creation(self):
        """Test creación de zona"""
        self.assertEqual(self.zone.name, "Terraza")
        self.assertTrue(self.zone.is_active)
        self.assertEqual(str(self.zone), "Terraza")


class TableModelTest(TestCase):
    """Tests para el modelo Table"""
    
    def setUp(self):
        self.zone = Zone.objects.create(name="Salón", display_order=1)
        self.table = Table.objects.create(
            zone=self.zone,
            number="M1",
            capacity=4,
            status='available'
        )
    
    def test_table_creation(self):
        """Test creación de mesa"""
        self.assertEqual(self.table.number, "M1")
        self.assertEqual(self.table.capacity, 4)
        self.assertEqual(self.table.status, 'available')
        self.assertTrue(self.table.is_active)
    
    def test_table_str(self):
        """Test representación en string"""
        self.assertEqual(str(self.table), "Mesa M1 - Salón")


class ZoneAPITest(TestCase):
    """Tests para la API de Zones"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.zone = Zone.objects.create(
            name="Test Zone",
            display_order=1
        )
    
    def test_list_zones(self):
        """Test listar zonas"""
        response = self.client.get('/api/zones/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_zone(self):
        """Test crear zona"""
        data = {
            'name': 'Nueva Zona',
            'description': 'Descripción',
            'display_order': 2,
            'is_active': True
        }
        response = self.client.post('/api/zones/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Zone.objects.count(), 2)
    
    def test_retrieve_zone(self):
        """Test obtener detalle de zona"""
        response = self.client.get(f'/api/zones/{self.zone.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Zone')


class TableAPITest(TestCase):
    """Tests para la API de Tables"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.zone = Zone.objects.create(name="Test Zone", display_order=1)
        self.table = Table.objects.create(
            zone=self.zone,
            number="T1",
            capacity=4
        )
    
    def test_list_tables(self):
        """Test listar mesas"""
        response = self.client.get('/api/tables/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_table(self):
        """Test crear mesa"""
        data = {
            'zone': self.zone.id,
            'number': 'T2',
            'capacity': 6,
            'status': 'available',
            'is_active': True
        }
        response = self.client.post('/api/tables/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Table.objects.count(), 2)
    
    def test_update_table_status(self):
        """Test actualizar estado de mesa"""
        data = {'status': 'occupied'}
        response = self.client.post(f'/api/tables/{self.table.id}/update_status/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, 'occupied')
