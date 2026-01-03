from .models import Category

def categories(request):
    """
    Context processor to make categories available in all templates.
    """
    return {
        'categories': Category.objects.filter(is_active=True)
    }
