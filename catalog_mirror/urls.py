from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MirroredProductViewSet, MirroredRecipeViewSet

router = DefaultRouter()
router.register(r'products', MirroredProductViewSet, basename='mirroredproduct')
router.register(r'recipes', MirroredRecipeViewSet, basename='mirroredrecipe')

app_name = 'catalog_mirror'

urlpatterns = [
    path('', include(router.urls)),
]
