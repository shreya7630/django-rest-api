from rest_framework import filters, viewsets
from .models import Category, Product
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer

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
        category = params.get('category')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        in_stock = params.get('in_stock')

        if category:
            queryset = queryset.filter(category_id=category)
        if min_price:
            queryset = queryset.filter(price_gte=min_price)
        if max_price:
            queryset = queryset.filter(price_lte=max_price)
        if in_stock == 'true':
            queryset = queryset.filter(stock_gt=0)
        
        return queryset