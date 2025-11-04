from rest_framework import serializers
from .models import MenuCategory, MenuItem, MenuItemComponent


class MenuItemComponentSerializer(serializers.ModelSerializer):
    component_name = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = MenuItemComponent
        fields = ['id', 'component_type', 'product_id', 'recipe_id', 
                  'quantity', 'cached_unit_cost', 'total_cost', 'component_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_component_name(self, obj):
        """Obtener el nombre del producto o receta desde catalog_mirror"""
        from catalog_mirror.models import MirroredProduct, MirroredRecipe
        
        if obj.component_type == 'product' and obj.product_id:
            try:
                product = MirroredProduct.objects.get(original_id=obj.product_id)
                return product.name
            except MirroredProduct.DoesNotExist:
                return f"Producto #{obj.product_id}"
        elif obj.component_type == 'recipe' and obj.recipe_id:
            try:
                recipe = MirroredRecipe.objects.get(original_id=obj.recipe_id)
                return recipe.name
            except MirroredRecipe.DoesNotExist:
                return f"Receta #{obj.recipe_id}"
        return "Desconocido"

    def get_total_cost(self, obj):
        return obj.get_cost()

    def validate(self, data):
        component_type = data.get('component_type')
        product_id = data.get('product_id')
        recipe_id = data.get('recipe_id')

        if component_type == 'product' and not product_id:
            raise serializers.ValidationError("product_id es requerido cuando component_type es 'product'")
        if component_type == 'recipe' and not recipe_id:
            raise serializers.ValidationError("recipe_id es requerido cuando component_type es 'recipe'")
        if product_id and recipe_id:
            raise serializers.ValidationError("No puede especificar product_id y recipe_id al mismo tiempo")

        return data


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    components = MenuItemComponentSerializer(many=True, read_only=True)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'category', 'category_name', 'name', 'description', 
                  'price', 'cached_cost', 'profit_margin', 'image_url', 
                  'is_available', 'display_order', 'preparation_time', 
                  'components', 'created_at', 'updated_at']
        read_only_fields = ['cached_cost', 'created_at', 'updated_at']


class MenuItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar MenuItem con componentes anidados"""
    components = MenuItemComponentSerializer(many=True, required=False)

    class Meta:
        model = MenuItem
        fields = ['id', 'category', 'name', 'description', 'price', 
                  'image_url', 'is_available', 'display_order', 
                  'preparation_time', 'components']

    def create(self, validated_data):
        components_data = validated_data.pop('components', [])
        menu_item = MenuItem.objects.create(**validated_data)
        
        for component_data in components_data:
            MenuItemComponent.objects.create(menu_item=menu_item, **component_data)
        
        menu_item.calculate_cost()
        return menu_item

    def update(self, instance, validated_data):
        components_data = validated_data.pop('components', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if components_data is not None:
            # Eliminar componentes existentes y crear nuevos
            instance.components.all().delete()
            for component_data in components_data:
                MenuItemComponent.objects.create(menu_item=instance, **component_data)
            
            instance.calculate_cost()
        
        return instance


class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'display_order', 'is_active', 
                  'items_count', 'items', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.filter(is_available=True).count()


class MenuCategoryListSerializer(serializers.ModelSerializer):
    """Versión simplificada sin items anidados para listados"""
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'display_order', 'is_active', 
                  'items_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_items_count(self, obj):
        return obj.items.filter(is_available=True).count()
