from rest_framework import serializers
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'title', 'price', 'quantity']


class GenerateReceiptSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(), required=True
    )
