import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProjectStore.settings')
django.setup()

from Store.models import Product

def youtube_embed_url_test(value):
    if not value:
        return ""
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]+)'
    match = re.search(regex, value)
    if match:
        video_id = match.group(1)
        # Capture until special characters if needed
        video_id = re.split(r'[?&/]', video_id)[0]
        return video_id
    return None

products = Product.objects.all()
for p in products:
    if p.youtube_video_url:
        extracted = youtube_embed_url_test(p.youtube_video_url)
        print(f"Name: {p.name}")
        print(f"Original: {p.youtube_video_url}")
        print(f"Extracted ID: {extracted}")
        if extracted:
             print(f"Embed URL: https://www.youtube.com/embed/{extracted}")
        print("-" * 20)
