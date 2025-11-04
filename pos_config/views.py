"""
Views para configuración del POS
"""
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import PaymentMethod, Printer
from .serializers import PaymentMethodSerializer, PrinterSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de métodos de pago
    GET /api/pos/payment-methods/ - Lista métodos de pago
    POST /api/pos/payment-methods/ - Crea método de pago
    GET /api/pos/payment-methods/{id}/ - Obtiene método específico
    PATCH /api/pos/payment-methods/{id}/ - Actualiza método
    DELETE /api/pos/payment-methods/{id}/ - Elimina método
    """
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        """Incluye request en el contexto del serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_permissions(self):
        """Solo admins pueden crear, actualizar o eliminar"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class PrinterViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de impresoras
    GET /api/pos/printers/ - Lista impresoras
    POST /api/pos/printers/ - Crea impresora
    GET /api/pos/printers/{id}/ - Obtiene impresora específica
    PATCH /api/pos/printers/{id}/ - Actualiza impresora
    DELETE /api/pos/printers/{id}/ - Elimina impresora
    """
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Solo admins pueden crear, actualizar o eliminar"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
