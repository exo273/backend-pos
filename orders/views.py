from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order, OrderItem, Payment
from .serializers import (
    OrderSerializer, OrderListSerializer, OrderCreateSerializer, OrderUpdateSerializer,
    OrderItemSerializer, OrderItemCreateSerializer,
    PaymentSerializer, PaymentCreateSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar órdenes.
    
    list: Listar todas las órdenes
    create: Crear una nueva orden con items
    retrieve: Obtener detalle completo de una orden
    update: Actualizar una orden
    partial_update: Actualizar parcialmente una orden
    destroy: Eliminar una orden (solo si está en estado pending)
    """
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.select_related('table', 'table__zone').prefetch_related(
            'items__menu_item', 'payments'
        )
        
        # Filtrar por mesa
        table_id = self.request.query_params.get('table')
        if table_id:
            queryset = queryset.filter(table_id=table_id)
        
        # Filtrar por estado
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtrar órdenes activas (no completadas ni canceladas)
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(status__in=['pending', 'preparing', 'ready'])
        
        # Filtrar por rango de fechas
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        # Buscar por número de orden o nombre de cliente
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_phone__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def perform_destroy(self, instance):
        """Solo permitir eliminar órdenes en estado pending"""
        if instance.status != 'pending':
            raise ValueError("Solo se pueden eliminar órdenes en estado 'pending'")
        
        # Liberar la mesa si está ocupada por esta orden
        if instance.table:
            other_active_orders = instance.table.orders.filter(
                status__in=['pending', 'preparing', 'ready']
            ).exclude(id=instance.id)
            
            if not other_active_orders.exists():
                instance.table.status = 'available'
                instance.table.save()
        
        instance.delete()

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Agregar un item a una orden existente"""
        order = self.get_object()
        
        if order.status not in ['pending', 'preparing']:
            return Response(
                {'error': 'No se pueden agregar items a una orden en este estado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(order=order)
            order.calculate_total()
            
            # Broadcast a KDS
            order.broadcast_to_kds()
            
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Eliminar un item de una orden"""
        order = self.get_object()
        
        if order.status not in ['pending']:
            return Response(
                {'error': 'No se pueden eliminar items de una orden en preparación o posterior'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = order.items.get(id=item_id)
            item.delete()
            order.calculate_total()
            
            return Response(OrderSerializer(order).data)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado en esta orden'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar el estado de una orden"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderUpdateSerializer(order, data={'status': new_status}, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Si se marca como delivered, liberar la mesa
            if new_status == 'delivered' and order.table:
                other_active = order.table.orders.filter(
                    status__in=['pending', 'preparing', 'ready']
                ).exclude(id=order.id)
                
                if not other_active.exists():
                    order.table.status = 'available'
                    order.table.save()
            
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Agregar un pago a una orden"""
        order = self.get_object()
        
        serializer = PaymentCreateSerializer(
            data=request.data,
            context={'order': order}
        )
        
        if serializer.is_valid():
            payment = serializer.save(order=order, status='completed')
            
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def kds(self, request):
        """Obtener órdenes para el Kitchen Display System"""
        orders = self.get_queryset().filter(
            status__in=['pending', 'preparing']
        ).order_by('created_at')
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Obtener resumen de órdenes del día"""
        today = timezone.now().date()
        orders = self.get_queryset().filter(created_at__date=today)
        
        summary = {
            'date': today.isoformat(),
            'total_orders': orders.count(),
            'by_status': {},
            'total_revenue': 0,
            'total_paid': 0,
            'pending_payment': 0,
        }
        
        # Por estado
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            summary['by_status'][status_code] = {
                'name': status_name,
                'count': count
            }
        
        # Totales financieros
        completed_orders = orders.filter(status='delivered')
        summary['total_revenue'] = float(completed_orders.aggregate(
            total=Sum('total')
        )['total'] or 0)
        
        # Total pagado
        from django.db.models import Sum as DSum
        total_paid = Payment.objects.filter(
            order__in=orders,
            status='completed'
        ).aggregate(total=DSum('amount'))['total'] or 0
        summary['total_paid'] = float(total_paid)
        
        summary['pending_payment'] = summary['total_revenue'] - summary['total_paid']
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def unpaid(self, request):
        """Obtener órdenes con pagos pendientes"""
        orders = []
        
        for order in self.get_queryset().filter(status__in=['pending', 'preparing', 'ready', 'delivered']):
            if not order.is_fully_paid:
                total_paid = sum(p.amount for p in order.payments.filter(status='completed'))
                orders.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'table': order.table.number if order.table else None,
                    'total': float(order.total),
                    'paid': float(total_paid),
                    'remaining': float(order.total - total_paid),
                    'status': order.status,
                })
        
        return Response(orders)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para pagos.
    Los pagos se crean a través del endpoint de órdenes.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.select_related('order')
        
        # Filtrar por orden
        order_id = self.request.query_params.get('order')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        # Filtrar por método de pago
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filtrar por estado
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtrar por fecha
        date_from = self.request.query_params.get('date_from')
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Resumen de pagos del día por método de pago"""
        today = timezone.now().date()
        payments = self.get_queryset().filter(
            created_at__date=today,
            status='completed'
        )
        
        summary = {
            'date': today.isoformat(),
            'total': float(payments.aggregate(Sum('amount'))['amount__sum'] or 0),
            'by_method': {}
        }
        
        for method_code, method_name in Payment.PAYMENT_METHOD_CHOICES:
            amount = payments.filter(payment_method=method_code).aggregate(
                Sum('amount')
            )['amount__sum'] or 0
            
            summary['by_method'][method_code] = {
                'name': method_name,
                'total': float(amount),
                'count': payments.filter(payment_method=method_code).count()
            }
        
        return Response(summary)
