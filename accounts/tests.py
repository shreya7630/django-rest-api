from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

PASSWORD = "Str0ng!Pass99"


class AuthTests(APITestCase):
    def register(self, username= 'asha', email='asha@example.com', password=PASSWORD):
        return self.client.post(
            '/api/auth/register/',
            {'username': username, 'email': email, 'password': password},
            format='json',
        )

    def test_register_stores_a_hashed_password(self):
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        user = User.objects.get(username='asha')
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_duplicate_email_is_rejected(self):
        self.register()
        response = self.register(username='other')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_is_rejected(self):
        response = self.register(password='123')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_access_and_refresh_tokens(self):
        User.objects.create_user('asha', 'asha@example.com', PASSWORD)
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'asha', 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user('asha', 'asha@example.com', PASSWORD)
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'asha', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_a_token(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_works_with_a_valid_token(self):
        User.objects.create_user('asha', 'asha@example.com', PASSWORD)
        login = self.client.post(
            '/api/auth/login/',
            {'username': 'asha', 'password': PASSWORD},
            format='json',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'asha')