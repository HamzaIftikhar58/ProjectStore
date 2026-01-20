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
class PerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        # Setup data
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.ai_category = Category.objects.create(name='AI', slug='ai')

        # Create products for Electronics
        products_electronics = []
        for i in range(10):
            products_electronics.append(Product(
                name=f'Product {i}',
                category=self.category,
                slug=f'product-{i}',
                sku=f'sku-{i}',
                price=10.00,
                stock=10,
                short_description='desc',
                description='desc',
                main_image='test.jpg'
            ))
        Product.objects.bulk_create(products_electronics)

        # Create products for AI
        products_ai = []
        for i in range(10):
            products_ai.append(Product(
                name=f'AI Product {i}',
                category=self.ai_category,
                slug=f'ai-product-{i}',
                sku=f'ai-sku-{i}',
                price=10.00,
                stock=10,
                short_description='desc',
                description='desc',
                main_image='test.jpg'
            ))
        Product.objects.bulk_create(products_ai)

    def test_category_products_performance(self):
        """
        Test that accessing category products page does not generate N+1 queries.
        """
        url = reverse('category_products', args=[self.category.slug])

        # Using CaptureQueriesContext from django.test.utils
        with CaptureQueriesContext(connection) as captured_queries:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            # Check for individual category fetches
            individual_fetches = [q['sql'] for q in captured_queries if 'WHERE "Store_category"."id" =' in q['sql']]

            self.assertEqual(len(individual_fetches), 0, f"Found {len(individual_fetches)} individual category fetches: {individual_fetches}")

    def test_AIpage_performance(self):
        """
        Test AIpage performance directly since it might not be in urls.py.
        """
        request = self.factory.get('/ai-page/')
        request.user = User.objects.create_user(username='testuser', password='password')

        # Add session and messages
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()

        from django.contrib.messages.middleware import MessageMiddleware
        middleware = MessageMiddleware(lambda r: None)
        middleware.process_request(request)

        with CaptureQueriesContext(connection) as captured_queries:
            response = AIpage(request)
            self.assertEqual(response.status_code, 200)

            individual_fetches = [q['sql'] for q in captured_queries if 'WHERE "Store_category"."id" =' in q['sql']]
            self.assertEqual(len(individual_fetches), 0, f"Found {len(individual_fetches)} individual category fetches in AIpage")
