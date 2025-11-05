from rest_framework import serializers
from .models import Zone, Table


class ZoneSerializer(serializers.ModelSerializer):
    tables_count = serializers.SerializerMethodField()
    available_tables = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = ['id', 'name', 'description', 'is_active', 
                  'tables_count', 'available_tables', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def to_internal_value(self, data):
        """Convertir campos del frontend al formato del backend"""
        # Mapear nombre -> name y descripcion -> description si vienen del frontend
        if 'nombre' in data:
            data['name'] = data.pop('nombre')
        if 'descripcion' in data:
            data['description'] = data.pop('descripcion')
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Agregar alias en la respuesta para compatibilidad con frontend"""
        data = super().to_representation(instance)
        data['nombre'] = data['name']
        data['descripcion'] = data['description']
        return data

    def get_tables_count(self, obj):
        return obj.tables.count()

    def get_available_tables(self, obj):
        return obj.tables.filter(status='available').count()


class TableSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    current_order = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ['id', 'zone', 'zone_name', 'number', 'capacity', 'status', 
                  'position_x', 'position_y',
                  'current_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def to_internal_value(self, data):
        """Convertir campos del frontend al formato del backend"""
        # Mapear campos en español a inglés
        if 'numero' in data:
            data['number'] = data.pop('numero')
        if 'zona' in data:
            data['zone'] = data.pop('zona')
        if 'capacidad' in data:
            data['capacity'] = data.pop('capacidad')
        if 'posicion_x' in data:
            data['position_x'] = data.pop('posicion_x')
        if 'posicion_y' in data:
            data['position_y'] = data.pop('posicion_y')
        # Eliminar campos que no están en el modelo
        data.pop('ancho', None)
        data.pop('alto', None)
        data.pop('forma', None)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Agregar alias en la respuesta para compatibilidad con frontend"""
        data = super().to_representation(instance)
        data['numero'] = data['number']
        data['zona'] = data['zone']
        data['capacidad'] = data['capacity']
        data['posicion_x'] = data.get('position_x')
        data['posicion_y'] = data.get('position_y')
        return data

    def get_current_order(self, obj):
        # Obtener la orden activa actual de la mesa
        from orders.models import Order
        order = obj.orders.filter(status__in=['pending', 'preparing', 'ready']).first()
        if order:
            return {
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'total': str(order.total),
            }
        return None


class TableStatusUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar solo el estado de una mesa"""
    status = serializers.ChoiceField(choices=Table.STATUS_CHOICES)

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save()
        return instance
