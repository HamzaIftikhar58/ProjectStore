import re
from django import template

register = template.Library()

@register.filter(name='youtube_embed_url')
def youtube_embed_url(value):
    if not value:
        return ""
    # Handles: watch?v=ID, youtu.be/ID, shorts/ID, embed/ID, v/ID, e/ID
    match = re.search(
        r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/'
        r'|.*[?&]v=)|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        value
    )
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    return value


@register.filter(name='youtube_video_id')
def youtube_video_id(value):
    if not value:
        return ""
    match = re.search(
        r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/'
        r'|.*[?&]v=)|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        value
    )
    if match:
        return match.group(1)
    return ""
