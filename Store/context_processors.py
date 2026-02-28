from .models import Category, SiteSetting

def categories(request):
    """
    Context processor to make categories and site settings available in all templates.
    """
    return {
        'categories': Category.objects.filter(is_active=True),
        'site_settings': SiteSetting.objects.first()
    }
