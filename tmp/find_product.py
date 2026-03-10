import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProjectStore.settings')
django.setup()

from Store.models import Product

products = Product.objects.filter(name__icontains='spider')
for p in products:
    print(f"Name: {p.name}, Slug: {p.slug}, Video URL: {p.youtube_video_url}")
