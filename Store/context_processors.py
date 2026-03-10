from .models import Category, SiteSetting
from django.contrib.sites.shortcuts import get_current_site

def categories(request):
    """
    Context processor to make categories and site settings available in all templates.
    """
    return {
        'categories': Category.objects.filter(is_active=True),
        'site_settings': SiteSetting.objects.first()
    }

def meta_pixel(request):
    """
    Context processor to make the Meta Pixel ID available in all templates.
    Fetches the ID from the SiteConfiguration model associated with the current site.
    """
    current_site = get_current_site(request)
    # Using getattr to safely check for the 'configuration' related object
    config = getattr(current_site, 'configuration', None)
    
    return {
        'META_PIXEL_ID': config.meta_pixel_id if config and config.meta_pixel_id else None
    }
