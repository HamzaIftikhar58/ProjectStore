from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product, Category

class ImageSitemap(Sitemap):
    protocol = "https"
    def get_urls(self, page=1, site=None, protocol=None):
        protocol = self.protocol or protocol
        domain = self.get_domain(site)
        urls = super().get_urls(page, site, protocol)
        for url in urls:
            item = url.get('item')
            if item and hasattr(item, 'main_image') and item.main_image:
                image_url = item.main_image.url
                if not image_url.startswith(('http', 'https')):
                    url['image'] = f"{protocol}://{domain}{image_url}"
                else:
                    url['image'] = image_url
        return urls

class ProductSitemap(ImageSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True, is_project=False)

    def lastmod(self, obj):
        return obj.updated_at

class ProjectSitemap(ImageSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True, is_project=True)

    def lastmod(self, obj):
        return obj.updated_at

class CategorySitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

class HomeSitemap(Sitemap):
    protocol = "https"
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)

class StaticViewSitemap(Sitemap):
    protocol = "https"
    priority = 0.3
    changefreq = "weekly"

    def items(self):
        return ['product', 'project', 'contact']

    def location(self, item):
        return reverse(item)
