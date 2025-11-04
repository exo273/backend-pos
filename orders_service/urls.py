"""
URL Configuration for orders_service project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints con prefijo /pos/
    path('api/pos/', include('pos.urls')),
    path('api/pos/menu/', include('menu.urls')),
    path('api/pos/orders/', include('orders.urls')),
    path('api/pos/catalog/', include('catalog_mirror.urls')),
]
