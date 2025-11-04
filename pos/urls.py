from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ZoneViewSet, TableViewSet

router = DefaultRouter()
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'tables', TableViewSet, basename='table')

app_name = 'pos'

urlpatterns = [
    path('', include(router.urls)),
]
