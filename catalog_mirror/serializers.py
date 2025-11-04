from rest_framework import serializers
from .models import MirroredProduct, MirroredRecipe


class MirroredProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = MirroredProduct
        fields = ['id', 'original_id', 'name', 'sku', 'unit_cost', 
                  'current_stock', 'unit_of_measure', 'is_active', 
                  'last_synced_at', 'created_at']
        read_only_fields = ['last_synced_at', 'created_at']


class MirroredRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MirroredRecipe
        fields = ['id', 'original_id', 'name', 'production_cost', 
                  'yield_quantity', 'yield_unit', 'cost_per_unit', 
                  'is_active', 'last_synced_at', 'created_at']
        read_only_fields = ['cost_per_unit', 'last_synced_at', 'created_at']
