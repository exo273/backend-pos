"""
URLs para configuración del POS
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentMethodViewSet, PrinterViewSet

router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet, basename='paymentmethod')
router.register(r'printers', PrinterViewSet, basename='printer')

urlpatterns = [
    path('', include(router.urls)),
]
