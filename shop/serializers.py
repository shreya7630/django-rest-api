from rest_framework import serializers
from .models import Category, Order, OrderItem, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'category', 'category_name', 'name', 'description', 'price', 'stock', 'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = ('create_at', 'updated_at')
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price_at_purchase')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'status', 'total_amount', 'created_at', 'items')


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset = Product.objects.filter(is_active=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        product_ids = [items['product'].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError('Each Product can appear only once.')
        return items