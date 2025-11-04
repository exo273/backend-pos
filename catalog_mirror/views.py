from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import MirroredProduct, MirroredRecipe
from .serializers import MirroredProductSerializer, MirroredRecipeSerializer


class MirroredProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para productos espejo.
    Los productos se sincronizan automáticamente desde el microservicio de operaciones.
    """
    queryset = MirroredProduct.objects.all()
    serializer_class = MirroredProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MirroredProduct.objects.all()
        
        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Buscar por nombre o SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search)
            )
        
        # Filtrar productos con stock bajo
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(current_stock__lt=10)  # Ajustar threshold según necesidad
        
        return queryset.order_by('name')

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Obtener productos con stock bajo"""
        threshold = float(request.query_params.get('threshold', 10))
        
        products = self.get_queryset().filter(
            current_stock__lt=threshold,
            is_active=True
        )
        
        serializer = self.get_serializer(products, many=True)
        return Response({
            'threshold': threshold,
            'count': products.count(),
            'products': serializer.data
        })

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """Ver en qué items del menú se usa este producto"""
        product = self.get_object()
        
        from menu.models import MenuItemComponent
        components = MenuItemComponent.objects.filter(
            component_type='product',
            product_id=product.original_id
        ).select_related('menu_item')
        
        menu_items = []
        for component in components:
            menu_items.append({
                'menu_item_id': component.menu_item.id,
                'menu_item_name': component.menu_item.name,
                'quantity_used': str(component.quantity),
                'cost_contribution': str(component.get_cost()),
            })
        
        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'used_in_items': menu_items,
            'total_items': len(menu_items)
        })


class MirroredRecipeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para recetas espejo.
    Las recetas se sincronizan automáticamente desde el microservicio de operaciones.
    """
    queryset = MirroredRecipe.objects.all()
    serializer_class = MirroredRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = MirroredRecipe.objects.all()
        
        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Buscar por nombre
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')

    @action(detail=True, methods=['get'])
    def usage(self, request, pk=None):
        """Ver en qué items del menú se usa esta receta"""
        recipe = self.get_object()
        
        from menu.models import MenuItemComponent
        components = MenuItemComponent.objects.filter(
            component_type='recipe',
            recipe_id=recipe.original_id
        ).select_related('menu_item')
        
        menu_items = []
        for component in components:
            menu_items.append({
                'menu_item_id': component.menu_item.id,
                'menu_item_name': component.menu_item.name,
                'quantity_used': str(component.quantity),
                'cost_contribution': str(component.get_cost()),
            })
        
        return Response({
            'recipe_id': recipe.id,
            'recipe_name': recipe.name,
            'used_in_items': menu_items,
            'total_items': len(menu_items)
        })
