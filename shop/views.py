from decimal import Decimal, InvalidOperation

from django.db.models import ProtectedError
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import Category, Order, Product
from .permissions import IsAdminOrReadOnly
from .serializers import (
    CategorySerializer,
    OrderCreateSerializer,
    OrderSerializer, 
    ProductSerializer,
)
from .services import place_order

def parse_int_param(params, name):
    value = params.get(name)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError({name: 'Must be a whole number.'})

def parse_decimal_param(params, name):
    value = params.get(name)
    if value in (None, ''):
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValidationError({name: 'Must be a number.'})
    if not number.is_finite():
        raise ValidationError({name: 'Must be a number.'})
    return number

class ProtectedDeleteMixin:
    protected_message = 'This item is in use and cannot be deleted.'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': self.protected_message},
                status=status.HTTP_409_CONFLICT,
            )


class CategoryViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    protected_message = 'This category still has products. Move or delete them first.'
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    protected_message = (
        'This product is part of existing orders and cannot be deleted.'
        'Set is_active to false instead.'
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'name', 'created_at']

    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('id')
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        params = self.request.query_params
        category = parse_int_param(params, 'category')
        min_price = parse_int_param(params, 'min_price')
        max_price = parse_int_param(params, 'max_price')

        if category is not None:
            queryset = queryset.filter(category_id=category)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        if params.get('in_stock') == 'true':
            queryset = queryset.filter(stock_gt=0)
        
        return queryset


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.prefetch_related('items__product').order_by('-created_at')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = place_order(request.user, serializer.validated_data['items'])
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)