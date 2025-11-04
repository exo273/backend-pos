from rest_framework import serializers
from .models import Zone, Table


class ZoneSerializer(serializers.ModelSerializer):
    tables_count = serializers.SerializerMethodField()
    available_tables = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = ['id', 'name', 'description', 'display_order', 'is_active', 
                  'tables_count', 'available_tables', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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
                  'current_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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
