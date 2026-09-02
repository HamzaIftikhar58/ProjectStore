from django.test import TestCase, Client, RequestFactory, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.db import connection
from Store.models import Category, Product, Order, OrderItem, BlogPost, ItemQuestion
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
        # We expect a constant number of queries regardless of order count (7 queries).
        with self.assertNumQueries(7):
             response = self.client.get('/order-history/')
             self.assertEqual(response.status_code, 200)


class RobotsTxtTest(TestCase):
    def test_robots_txt(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        content = response.content.decode('utf-8')
        self.assertIn('User-agent: *', content)
        self.assertIn('Sitemap: https://projectstore.pk/sitemap.xml', content)
        # Check AI Bot rules
        self.assertIn('User-agent: GPTBot', content)
        self.assertIn('User-agent: PerplexityBot', content)
        self.assertIn('User-agent: ClaudeBot', content)
        self.assertIn('Allow: /llms.txt', content)


class AIOptimizationTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Robotics & Motors', slug='robotics-motors')
        self.product = Product.objects.create(
            name='L298N Motor Driver Module',
            category=self.category,
            slug='l298n-motor-driver',
            sku='ai97450',
            price=450.00,
            stock=50,
            availability=True,
            is_active=True,
            short_description='Dual H-Bridge Motor Driver Module for Arduino and Raspberry Pi.',
            description='High power L298N motor driver.',
            main_image='products/main/default.jpg'
        )

    def test_llms_txt_standard_endpoint(self):
        response = self.client.get('/llms.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        content = response.content.decode('utf-8')
        self.assertIn('# ProjectStore.pk', content)
        self.assertIn('Cash on Delivery (COD)', content)
        self.assertIn('https://projectstore.pk/product/', content)

    def test_llms_full_txt_catalog_endpoint(self):
        response = self.client.get('/llms-full.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        content = response.content.decode('utf-8')
        self.assertIn('L298N Motor Driver Module', content)
        self.assertIn('ai97450', content)
        self.assertIn('PKR 450.00', content)

    def test_home_page_faq_and_website_schema(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('"@type": "FAQPage"', content)
        self.assertIn('"@type": "OnlineStore"', content)
        self.assertIn('"@type": "SearchAction"', content)
        self.assertIn('Cash on Delivery', content)



class CanonicalDomainMiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_www_subdomain_redirects_301_to_apex(self):
        # Testing www.projectstore.pk redirection to https://projectstore.pk/contact/
        response = self.client.get('/contact/', HTTP_HOST='www.projectstore.pk')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://projectstore.pk/contact/')

    def test_www_product_redirects_301_preserving_query(self):
        response = self.client.get('/product/?page=2', HTTP_HOST='www.projectstore.pk')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://projectstore.pk/product/?page=2')


class CatalogAndProductSEOTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sensors & Modules', slug='sensors-modules')
        self.product = Product.objects.create(
            name='ESP32 Development Board WiFi Bluetooth',
            category=self.category,
            slug='esp32-development-board',
            sku='ai78432',
            price=1250.00,
            stock=25,
            availability=True,
            is_active=True,
            is_project=False,
            short_description='ESP32 NodeMCU WiFi + Bluetooth dual-core development board.',
            description='High performance ESP32 development board for IoT projects.',
            main_image='products/main/default.jpg'
        )

    def test_catalog_title_and_meta_description(self):
        response = self.client.get('/product/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<title>Premium DIY Store | Electronic Kits, Components & Software Codes | ProjectStore.pk</title>', content)
        self.assertIn("Pakistan's premium DIY store. Buy complete DIY kits", content)
        self.assertIn('<link rel="canonical" href="https://projectstore.pk/product/" />', content)

    def test_product_detail_json_ld_schema(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Check JSON-LD Product schema
        self.assertIn('"@type": "Product"', content)
        self.assertIn('"sku": "ai78432"', content)
        self.assertIn('"priceCurrency": "PKR"', content)
        self.assertIn('"availability": "https://schema.org/InStock"', content)
        self.assertIn('"name": "ProjectStore.pk"', content)
        self.assertIn('https://schema.org/NewCondition', content)
        # Check Return Policy in Schema
        self.assertIn('hasMerchantReturnPolicy', content)
        self.assertIn('https://projectstore.pk/return-policy/', content)

    def test_return_policy_page(self):
        response = self.client.get('/return-policy/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Return & Refund Policy', content)
        self.assertIn('7-Day Free Replacement Guarantee', content)

    def test_google_merchant_feed_return_policy(self):
        response = self.client.get('/feeds/google/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('<g:return_policy_label>7_day_return</g:return_policy_label>', content)
        self.assertIn('<g:shipping>', content)
        self.assertIn('<g:price>250.00 PKR</g:price>', content)


class BlogPostAndTutorialsTest(TestCase):
    def setUp(self):
        self.category, _ = Category.objects.get_or_create(
            slug='test-blog-category',
            defaults={'name': 'Test Blog Category'}
        )
        self.product, _ = Product.objects.get_or_create(
            sku='Test-Blog-Elec-1',
            defaults={
                'name': 'ESP32-WROOM-32 Development Board',
                'category': self.category,
                'slug': 'test-blog-esp32-wroom-32',
                'price': 1250.00,
                'stock': 50,
                'availability': True,
                'is_active': True,
                'short_description': 'ESP32 Dual-Core WiFi BLE Board.',
                'description': 'High performance ESP32 development board.'
            }
        )
        self.post, _ = BlogPost.objects.get_or_create(
            slug='test-esp32-vs-esp8266-comparison-guide',
            defaults={
                'title': 'ESP32 vs ESP8266 Comparison & Pinout Guide',
                'category': 'iot-embedded',
                'excerpt': 'Complete technical breakdown of ESP32 vs ESP8266 microcontrollers in Pakistan.',
                'content': '<p>Full tutorial comparing ESP32 and ESP8266 specs and pinouts.</p>',
                'author': 'ISOL Embedded Labs',
                'reading_time': '5 min read',
                'is_featured': True,
                'is_published': True
            }
        )
        self.post.related_products.add(self.product)

    def test_blog_list_view(self):
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Project Guides', content)
        self.assertIn('ESP32 vs ESP8266 Comparison', content)
        self.assertIn('ISOL Embedded Labs', content)

    def test_blog_list_category_filter(self):
        response = self.client.get('/blog/?category=iot-embedded')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('ESP32 vs ESP8266 Comparison', content)

    def test_blog_detail_view_and_product_embedding(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Check title and content
        self.assertIn('ESP32 vs ESP8266 Comparison', content)
        self.assertIn('Full tutorial comparing ESP32 and ESP8266 specs', content)
        # Check Schema.org TechArticle
        self.assertIn('"@type": "TechArticle"', content)
        self.assertIn('ISOL', content)
        # Check embedded product widget
        self.assertIn('ESP32-WROOM-32 Development Board', content)
        self.assertIn('PKR 1250', content)
        self.assertIn('Test-Blog-Elec-1', content)

    def test_blog_sitemap_integration(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn(self.post.get_absolute_url(), content)

    def test_llms_full_txt_includes_blog(self):
        response = self.client.get('/llms-full.txt')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('## Engineering Guides, Tutorials & FYP Architectures', content)
        self.assertIn('ESP32 vs ESP8266 Comparison & Pinout Guide', content)


class CommunityQATest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_student_lahore', password='password123', first_name='Usman')
        self.category, _ = Category.objects.get_or_create(slug='qa-test-cat', defaults={'name': 'QA Category'})
        self.product, _ = Product.objects.get_or_create(
            sku='QA-PROD-1',
            defaults={
                'name': 'ESP32 IoT Starter Board',
                'category': self.category,
                'slug': 'qa-esp32-starter-board',
                'price': 1200.0,
                'stock': 10,
                'availability': True,
                'is_active': True,
                'short_description': 'Test board for Q&A',
                'main_image': 'products/main/default.jpg'
            }
        )
        self.post, _ = BlogPost.objects.get_or_create(
            slug='qa-test-tutorial-guide',
            defaults={
                'title': 'How to Build IoT Smart Light with ESP32',
                'category': 'iot-embedded',
                'excerpt': 'Step by step smart light tutorial',
                'content': '<p>Full tutorial</p>',
                'author': 'ISOL Engineering',
                'reading_time': '4 min read',
                'is_published': True
            }
        )
        self.qa_product = ItemQuestion.objects.create(
            user=self.user,
            product=self.product,
            question='AOA sir, is COD available for Rawalpindi?',
            answer='Walaikum Assalam! Yes, COD takes 24-48 hours via TCS Courier.',
            is_approved=True
        )
        self.qa_blog = ItemQuestion.objects.create(
            user=self.user,
            blog_post=self.post,
            question='Can I use Arduino IDE version 2.0 for this code?',
            answer='Yes, Arduino IDE 2.x is fully supported.',
            is_approved=True
        )

    def test_ask_question_unauthenticated_returns_401(self):
        response = self.client.post('/ask-question/', {
            'product_id': self.product.id,
            'question': 'Is this available?'
        })
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertTrue(data['login_required'])

    def test_ask_question_authenticated_success(self):
        self.client.login(username='test_student_lahore', password='password123')
        response = self.client.post('/ask-question/', {
            'product_id': self.product.id,
            'question': 'Bhai Python version 3.11 chal jaye ga?'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['username'], 'Usman')
        self.assertIn('Python version 3.11', data['question'])
        self.assertTrue(ItemQuestion.objects.filter(question__icontains='Python version 3.11').exists())

    def test_product_detail_renders_qa_and_schema(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # Check rendered question and answer
        self.assertIn('is COD available for Rawalpindi?', content)
        self.assertIn('Walaikum Assalam! Yes, COD takes 24-48 hours', content)
        self.assertIn('ISOL Engineering Team', content)
        # Check FAQPage Schema for AI Overviews
        self.assertIn('"@type": "FAQPage"', content)

    def test_blog_detail_renders_qa_and_schema(self):
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('Can I use Arduino IDE version 2.0 for this code?', content)
        self.assertIn('Yes, Arduino IDE 2.x is fully supported.', content)
        self.assertIn('"@type": "FAQPage"', content)


