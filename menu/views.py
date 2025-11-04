from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Sum
from .models import MenuCategory, MenuItem, MenuItemComponent
from .serializers import (
    MenuCategorySerializer, MenuCategoryListSerializer,
    MenuItemSerializer, MenuItemCreateUpdateSerializer,
    MenuItemComponentSerializer
)


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar categorías del menú.
    
    list: Listar todas las categorías
    create: Crear una nueva categoría
    retrieve: Obtener detalle de una categoría con sus items
    update: Actualizar una categoría
    partial_update: Actualizar parcialmente una categoría
    destroy: Eliminar una categoría
    """
    queryset = MenuCategory.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return MenuCategoryListSerializer
        return MenuCategorySerializer

    def get_queryset(self):
        queryset = MenuCategory.objects.all()
        
        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('display_order', 'name')

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Obtener todos los items de una categoría específica"""
        category = self.get_object()
        items = category.items.filter(is_available=True)
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data)


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar items del menú.
    
    list: Listar todos los items
    create: Crear un nuevo item con sus componentes
    retrieve: Obtener detalle de un item con sus componentes
    update: Actualizar un item
    partial_update: Actualizar parcialmente un item
    destroy: Eliminar un item
    """
    queryset = MenuItem.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MenuItemCreateUpdateSerializer
        return MenuItemSerializer

    def get_queryset(self):
        queryset = MenuItem.objects.select_related('category').prefetch_related('components')
        
        # Filtrar por categoría
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filtrar por disponibilidad
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        # Buscar por nombre
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('category__display_order', 'display_order', 'name')

    @action(detail=True, methods=['post'])
    def recalculate_cost(self, request, pk=None):
        """Recalcular el costo de un item basado en sus componentes"""
        item = self.get_object()
        new_cost = item.calculate_cost()
        
        return Response({
            'id': item.id,
            'name': item.name,
            'cached_cost': item.cached_cost,
            'profit_margin': item.profit_margin,
            'message': f'Costo recalculado: ${new_cost}'
        })

    @action(detail=True, methods=['post'])
    def add_component(self, request, pk=None):
        """Agregar un componente a un item del menú"""
        item = self.get_object()
        serializer = MenuItemComponentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(menu_item=item)
            item.calculate_cost()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_component(self, request, pk=None):
        """Eliminar un componente de un item del menú"""
        item = self.get_object()
        component_id = request.data.get('component_id')
        
        if not component_id:
            return Response(
                {'error': 'component_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            component = item.components.get(id=component_id)
            component.delete()
            item.calculate_cost()
            
            return Response({
                'message': 'Componente eliminado exitosamente',
                'new_cost': item.cached_cost
            })
        except MenuItemComponent.DoesNotExist:
            return Response(
                {'error': 'Componente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Obtener solo los items disponibles (para el menú público)"""
        items = self.get_queryset().filter(is_available=True)
        
        # Agrupar por categoría
        categories = MenuCategory.objects.filter(
            is_active=True,
            items__in=items
        ).distinct().order_by('display_order')
        
        data = []
        for category in categories:
            category_items = items.filter(category=category)
            data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'items': MenuItemSerializer(category_items, many=True).data
            })
        
        return Response(data)

    @action(detail=False, methods=['post'])
    def recalculate_all_costs(self, request):
        """Recalcular los costos de todos los items del menú"""
        items = self.get_queryset()
        count = 0
        
        for item in items:
            item.calculate_cost()
            count += 1
        
        return Response({
            'message': f'Se recalcularon los costos de {count} items',
            'total_items': count
        })

    @action(detail=False, methods=['get'])
    def low_margin(self, request):
        """Obtener items con bajo margen de ganancia"""
        threshold = float(request.query_params.get('threshold', 20))  # 20% por defecto
        
        items = []
        for item in self.get_queryset():
            if item.profit_margin < threshold:
                items.append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'cost': item.cached_cost,
                    'profit_margin': float(item.profit_margin),
                })
        
        return Response({
            'threshold': threshold,
            'count': len(items),
            'items': items
        })


class MenuItemComponentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar componentes de items del menú.
    """
    queryset = MenuItemComponent.objects.all()
    serializer_class = MenuItemComponentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MenuItemComponent.objects.select_related('menu_item')
        
        # Filtrar por menu item
        menu_item_id = self.request.query_params.get('menu_item')
        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)
        
        # Filtrar por tipo de componente
        component_type = self.request.query_params.get('component_type')
        if component_type:
            queryset = queryset.filter(component_type=component_type)
        
        return queryset
