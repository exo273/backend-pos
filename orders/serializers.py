from rest_framework import serializers
from .models import Order, OrderItem, Payment
from menu.serializers import MenuItemSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_details = MenuItemSerializer(source='menu_item', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_details',
                  'quantity', 'unit_price', 'subtotal', 'notes', 'created_at']
        read_only_fields = ['unit_price', 'subtotal', 'created_at']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear OrderItems"""
    
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'notes']

    def validate_menu_item(self, value):
        if not value.is_available:
            raise serializers.ValidationError(f"El item '{value.name}' no está disponible actualmente")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'payment_method', 'payment_method_display', 
                  'amount', 'status', 'status_display', 
                  'convenio_code', 'convenio_name', 'transaction_reference', 
                  'notes', 'created_at', 'completed_at']
        read_only_fields = ['created_at', 'completed_at']

    def validate(self, data):
        if data.get('payment_method') == 'convenio' and not data.get('convenio_code'):
            raise serializers.ValidationError({
                'convenio_code': 'Este campo es requerido para pagos con convenio'
            })
        return data


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pagos"""
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount', 'convenio_code', 'convenio_name', 
                  'transaction_reference', 'notes']

    def validate(self, data):
        if data.get('payment_method') == 'convenio' and not data.get('convenio_code'):
            raise serializers.ValidationError({
                'convenio_code': 'Este campo es requerido para pagos con convenio'
            })
        
        # Validar que el monto no exceda el total pendiente de la orden
        order = self.context.get('order')
        if order:
            total_paid = sum(p.amount for p in order.payments.filter(status='completed'))
            remaining = order.total - total_paid
            if data['amount'] > remaining:
                raise serializers.ValidationError({
                    'amount': f'El monto excede el total pendiente de ${remaining}'
                })
        
        return data


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    table_number = serializers.CharField(source='table.number', read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    total_paid = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'table', 'table_number', 'status', 'status_display',
                  'customer_name', 'customer_phone', 'notes',
                  'subtotal', 'tax', 'total', 'is_fully_paid', 
                  'total_paid', 'remaining_amount',
                  'items', 'payments',
                  'created_at', 'started_at', 'completed_at', 'updated_at']
        read_only_fields = ['order_number', 'subtotal', 'tax', 'total', 
                            'created_at', 'started_at', 'completed_at', 'updated_at']

    def get_total_paid(self, obj):
        return sum(p.amount for p in obj.payments.filter(status='completed'))

    def get_remaining_amount(self, obj):
        total_paid = self.get_total_paid(obj)
        return obj.total - total_paid


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear órdenes con items anidados"""
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['table', 'customer_name', 'customer_phone', 'notes', 'items']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un item en la orden")
        return value

    def validate_table(self, value):
        if value and value.status != 'available':
            # Permitir si la mesa ya tiene una orden activa del mismo cliente
            existing_order = value.orders.filter(
                status__in=['pending', 'preparing', 'ready']
            ).first()
            if existing_order:
                # Se puede agregar lógica adicional aquí si se necesita
                pass
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        order.calculate_total()
        
        # Cambiar el estado de la mesa si aplica
        if order.table:
            order.table.status = 'occupied'
            order.table.save()
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar órdenes"""
    
    class Meta:
        model = Order
        fields = ['status', 'customer_name', 'customer_phone', 'notes']

    def validate_status(self, value):
        # Validar transiciones de estado permitidas
        if self.instance:
            current_status = self.instance.status
            
            # No se puede volver a estados anteriores (excepto de preparing a pending)
            status_order = {
                'pending': 0,
                'preparing': 1,
                'ready': 2,
                'delivered': 3,
                'cancelled': 4
            }
            
            if value not in ['pending', 'cancelled']:
                if status_order.get(value, 0) < status_order.get(current_status, 0):
                    if not (current_status == 'preparing' and value == 'pending'):
                        raise serializers.ValidationError(
                            f"No se puede cambiar de '{current_status}' a '{value}'"
                        )
            
            # No se puede modificar una orden cancelada o entregada
            if current_status in ['cancelled', 'delivered']:
                raise serializers.ValidationError(
                    f"No se puede modificar una orden con estado '{current_status}'"
                )
        
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de órdenes"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    table_number = serializers.CharField(source='table.number', read_only=True)
    items_count = serializers.SerializerMethodField()
    is_fully_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'table_number', 'status', 'status_display',
                  'customer_name', 'total', 'is_fully_paid', 'items_count',
                  'created_at', 'updated_at']
        read_only_fields = ['order_number', 'created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.count()
