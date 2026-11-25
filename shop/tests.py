from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Order, Product

User = get_user_model()

PASSWORD = 'Str0ng!Pass99'


class ShopTestBase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'admin', 'admin@example.com', PASSWORD, is_staff=True
        )
        self.customer = User.objects.create_user('asha', 'asha@example.com', PASSWORD)
        self.category = Category.objects.create(name='Earrings')
        self.hoops = Product.objects.create(
            category=self.category, name='Silver Hoops',
            price=Decimal('500.00'), stock=5,
        )
        self.studs = Product.objects.create(
            category=self.category, name='Pearl Studs',
            price=Decimal('300.00'), stock=2,
        )


class ProductTests(ShopTestBase):
    def new_product_data(self):
        return {
            'category': self.category.id,
            'name': 'Gold Charm',
            'price': '250.00',
            'stock': 10,
        }

    def test_anyone_can_list_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_anonymous_cannot_create_product(self):
        response = self.client.post('/api/products/', self.new_product_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post('/api/products/', self.new_product_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/products/', self.new_product_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 3)

    def test_negative_price_is_rejected(self):
        self.client.force_authenticate(self.admin)
        data = self.new_product_data()
        data['price'] = '-5'
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_products_are_hidden_from_customers(self):
        self.studs.is_active = False
        self.studs.save()
        response = self.client.get('/api/products/')
        self.assertEqual(response.data['count'], 1)

    def test_price_filter_returns_only_matching_products(self):
        response = self.client.get('/api/products/?min_price=400')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Silver Hoops')

    def test_invalid_price_filter_returns_400(self):
        response = self.client.get('/api/products/?min_price=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_delete_category_that_has_products(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f'/api/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)