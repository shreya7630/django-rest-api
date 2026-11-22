from decimal import Decimal, InvalidOperation

from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError

from .models import Category, Product
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer

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


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
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