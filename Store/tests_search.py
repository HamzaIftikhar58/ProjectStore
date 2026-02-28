from django.test import Client, TestCase, override_settings
from django.urls import reverse
from Store.models import Product, Category
from django.core.files.uploadedfile import SimpleUploadedFile

@override_settings(STORAGES={
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
})
class SearchTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="TestCat", slug="test-cat")

        # Create a dummy image
        image = SimpleUploadedFile("small.gif", b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x3b', content_type="image/gif")

        # Create a product
        Product.objects.create(
            name="Test Product",
            category=cat,
            slug="test-product",
            sku="TP001",
            short_description="Desc",
            description="Desc",
            price=10.00,
            stock=10,
            is_project=False,
            is_active=True,
            main_image=image
        )

        # Create a project
        Product.objects.create(
            name="Test Project",
            category=cat,
            slug="test-project",
            sku="TP002",
            short_description="Desc",
            description="Desc",
            price=20.00,
            stock=10,
            is_project=True,
            is_active=True,
            main_image=image
        )

    def test_search_includes_project(self):
        response = self.client.get(reverse('product'), {'q': 'Project'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")
        # Ensure that searching for "Project" doesn't return "Test Product" (unless "Product" contains "Project", which it doesn't)
        self.assertNotContains(response, "Test Product")

    def test_search_includes_product(self):
        response = self.client.get(reverse('product'), {'q': 'Product'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertNotContains(response, "Test Project")
