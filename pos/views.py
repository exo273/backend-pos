from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from .models import Zone, Table
from .serializers import ZoneSerializer, TableSerializer, TableStatusUpdateSerializer


class ZoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar zonas del restaurante.
    
    list: Listar todas las zonas
    create: Crear una nueva zona
    retrieve: Obtener detalle de una zona
    update: Actualizar una zona
    partial_update: Actualizar parcialmente una zona
    destroy: Eliminar una zona
    """
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Zone.objects.all()
        
        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('display_order', 'name')

    @action(detail=True, methods=['get'])
    def tables(self, request, pk=None):
        """Obtener todas las mesas de una zona específica"""
        zone = self.get_object()
        tables = zone.tables.filter(is_active=True)
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def with_stats(self, request):
        """Obtener zonas con estadísticas de mesas"""
        zones = self.get_queryset().annotate(
            total_tables=Count('tables'),
            available_tables_count=Count('tables', filter=Q(tables__status='available'))
        )
        
        data = []
        for zone in zones:
            zone_data = ZoneSerializer(zone).data
            zone_data['stats'] = {
                'total_tables': zone.total_tables,
                'available_tables': zone.available_tables_count,
                'occupied_tables': zone.total_tables - zone.available_tables_count
            }
            data.append(zone_data)
        
        return Response(data)


class TableViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar mesas del restaurante.
    
    list: Listar todas las mesas
    create: Crear una nueva mesa
    retrieve: Obtener detalle de una mesa
    update: Actualizar una mesa
    partial_update: Actualizar parcialmente una mesa
    destroy: Eliminar una mesa
    """
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Table.objects.select_related('zone').all()
        
        # Filtrar por zona
        zone_id = self.request.query_params.get('zone')
        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        
        # Filtrar por estado
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('zone__display_order', 'number')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Actualizar solo el estado de una mesa"""
        table = self.get_object()
        serializer = TableStatusUpdateSerializer(table, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(TableSerializer(table).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_available(self, request, pk=None):
        """Marcar una mesa como disponible"""
        table = self.get_object()
        
        # Verificar que no tenga órdenes activas
        from orders.models import Order
        active_orders = table.orders.filter(status__in=['pending', 'preparing', 'ready'])
        
        if active_orders.exists():
            return Response(
                {'error': 'No se puede marcar como disponible. La mesa tiene órdenes activas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        table.status = 'available'
        table.save()
        
        return Response(TableSerializer(table).data)

    @action(detail=True, methods=['post'])
    def mark_occupied(self, request, pk=None):
        """Marcar una mesa como ocupada"""
        table = self.get_object()
        table.status = 'occupied'
        table.save()
        return Response(TableSerializer(table).data)

    @action(detail=True, methods=['post'])
    def mark_reserved(self, request, pk=None):
        """Marcar una mesa como reservada"""
        table = self.get_object()
        table.status = 'reserved'
        table.save()
        return Response(TableSerializer(table).data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtener solo las mesas disponibles"""
        tables = self.get_queryset().filter(status='available', is_active=True)
        serializer = self.get_serializer(tables, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """Obtener resumen de estados de todas las mesas"""
        queryset = self.get_queryset().filter(is_active=True)
        
        summary = {
            'total': queryset.count(),
            'available': queryset.filter(status='available').count(),
            'occupied': queryset.filter(status='occupied').count(),
            'reserved': queryset.filter(status='reserved').count(),
        }
        
        # Por zona
        zones_summary = []
        from .models import Zone
        for zone in Zone.objects.filter(is_active=True):
            zone_tables = queryset.filter(zone=zone)
            zones_summary.append({
                'zone_id': zone.id,
                'zone_name': zone.name,
                'total': zone_tables.count(),
                'available': zone_tables.filter(status='available').count(),
                'occupied': zone_tables.filter(status='occupied').count(),
                'reserved': zone_tables.filter(status='reserved').count(),
            })
        
        summary['by_zone'] = zones_summary
        
        return Response(summary)
