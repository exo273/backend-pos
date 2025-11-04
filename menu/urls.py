from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuCategoryViewSet, MenuItemViewSet, MenuItemComponentViewSet

router = DefaultRouter()
router.register(r'categories', MenuCategoryViewSet, basename='menucategory')
router.register(r'items', MenuItemViewSet, basename='menuitem')
router.register(r'components', MenuItemComponentViewSet, basename='menuitemcomponent')

app_name = 'menu'

urlpatterns = [
    path('', include(router.urls)),
]
