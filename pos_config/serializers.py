"""
Serializers para configuración del POS
"""
from rest_framework import serializers
from .models import PaymentMethod, Printer


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer para métodos de pago"""
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'logo', 'logo_url', 'is_active', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_logo_url(self, obj):
        """Retorna la URL completa del logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class PrinterSerializer(serializers.ModelSerializer):
    """Serializer para impresoras"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    connection_display = serializers.CharField(source='get_connection_type_display', read_only=True)
    
    class Meta:
        model = Printer
        fields = [
            'id', 'name', 'type', 'type_display', 'connection_type', 'connection_display',
            'ip_address', 'port', 'is_active', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Valida que si la conexión es de red, debe tener IP"""
        connection_type = attrs.get('connection_type')
        ip_address = attrs.get('ip_address')
        
        if connection_type == 'network' and not ip_address:
            raise serializers.ValidationError({
                'ip_address': 'Se requiere dirección IP para conexiones de red.'
            })
        
        return attrs
