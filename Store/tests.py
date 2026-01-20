from django.test import TestCase, Client, RequestFactory, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.db import connection
from Store.models import Category, Product
from Store.views import AIpage
from django.contrib.auth.models import User

@override_settings(STORAGES={
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
})
class OrderHistoryPerformanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='perf_test_user', password='password')
        self.category = Category.objects.create(name='Test Category', slug='test-category')

        self.products = []
        for i in range(10):
            p = Product.objects.create(
                name=f'Product {i}',
                category=self.category,
                slug=f'product-{i}',
                sku=f'SKU-{i}',
                price=100,
                stock=10,
                description='Desc',
                short_description='Short Desc',
                main_image='products/main/default.jpg'
            )
            self.products.append(p)

        # Create 10 Orders, each with 5 Items
        for i in range(10):
            order = Order.objects.create(
                user=self.user,
                email='test@example.com',
                total=500,
                country='Country',
                city='City',
                state='State',
                zip_code='12345',
                phone='1234567890',
                address='Address',
                payment_method='online_payment'
            )
            for j in range(5):
                OrderItem.objects.create(
                    order=order,
                    product=self.products[j],
                    quantity=1,
                    price=100
                )

        self.client = Client()
        self.client.login(username='perf_test_user', password='password')

    def test_order_history_query_count(self):
        # We expect a constant number of queries regardless of order count.
        # Queries:
        # 1. Session lookup (middleware)
        # 2. User lookup (middleware)
        # 3. Order query
        # 4. OrderItem prefetch
        # 5. Product prefetch
        # 6. Variant prefetch
        # Total: 6
        with self.assertNumQueries(6):
             response = self.client.get('/order-history/')
             self.assertEqual(response.status_code, 200)
