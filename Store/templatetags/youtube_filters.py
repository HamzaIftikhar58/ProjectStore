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


@register.filter(name='seo_title')
def seo_title(value, max_len=60):
    """
    Formats product/item titles to stay strictly within max_len (default 60 chars)
    to satisfy search engine guidelines (Bing <= 65 chars, Google 50-60 chars).
    Strips subtitle pipes and truncates cleanly at word boundaries.
    """
    if not value:
        return "ProjectStore.pk"
    
    brand_suffix = " | ProjectStore.pk"
    avail = max_len - len(brand_suffix)  # e.g. 60 - 17 = 43 chars
    
    # Strip marketing subtitles after pipes or colons if too long
    clean = str(value).split('|')[0].strip()
    
    candidate_with_buy = f"Buy {clean}{brand_suffix}"
    if len(candidate_with_buy) <= max_len:
        return candidate_with_buy
        
    candidate_no_buy = f"{clean}{brand_suffix}"
    if len(candidate_no_buy) <= max_len:
        return candidate_no_buy
        
    # Truncate at word boundary
    truncated = clean[:avail].rsplit(' ', 1)[0]
    return f"{truncated}{brand_suffix}"

