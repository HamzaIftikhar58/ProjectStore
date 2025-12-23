# your_app/templatetags/youtube_filters.py
from django import template

register = template.Library()

def youtube_embed_url(value):
    if not value:
        return ""
    if "youtu.be" in value:
        video_id = value.split("/")[-1].split("?")[0]  # Extracts video ID from youtu.be
    elif "watch?v=" in value:
        video_id = value.split("watch?v=")[1].split("?")[0]  # Extracts video ID from youtube.com/watch
    else:
        return value  # Return as is if already an embed URL
    return f"https://www.youtube.com/embed/{video_id}"

register.filter('youtube_embed_url', youtube_embed_url)