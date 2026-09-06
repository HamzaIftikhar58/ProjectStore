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
    truncated = clean[:avail].rsplit(' ', 1)[0].rstrip(':, -/(&')
    if '(' in truncated and ')' not in truncated:
        truncated = truncated.split('(')[0].strip().rstrip(':, -/(&')
    return f"{truncated}{brand_suffix}"


@register.filter(name='blog_seo_title')
def blog_seo_title(post, max_len=65):
    """
    Formats blog titles cleanly under 65 chars.
    Prevents duplicate '| ProjectStore.pk' suffixes and trims neatly at word boundaries.
    """
    if not post:
        return "Project Guides & FYP Ideas | ProjectStore.pk"
    
    brand = " | ProjectStore.pk"
    raw = getattr(post, 'meta_title', None) or getattr(post, 'title', str(post))
    raw = str(raw).strip()
    
    # Strip any existing brand suffix
    clean = raw
    if clean.endswith(brand):
        clean = clean[:-len(brand)].strip()
    elif clean.endswith("| ProjectStore.pk"):
        clean = clean[:-len("| ProjectStore.pk")].strip()
        
    # Strip pipe subtitles and parenthetical remarks if needed
    clean = clean.split('|')[0].strip()
    clean = re.sub(r'\s*\([^)]*\)', '', clean).strip()
    
    # Shorten common long phrases if close to limit
    if clean.lower().startswith('how to build an '):
        shortened = 'Build ' + clean[16:]
        if len(f"{shortened}{brand}") <= max_len:
            return f"{shortened}{brand}"
    elif clean.lower().startswith('how to build '):
        shortened = 'Build ' + clean[13:]
        if len(f"{shortened}{brand}") <= max_len:
            return f"{shortened}{brand}"
            
    full = f"{clean}{brand}"
    if len(full) <= max_len:
        return full
        
    # Truncate at word boundary
    avail = max_len - len(brand)
    trimmed = clean[:avail].rsplit(' ', 1)[0].rstrip(':, -')
    return f"{trimmed}{brand}"


