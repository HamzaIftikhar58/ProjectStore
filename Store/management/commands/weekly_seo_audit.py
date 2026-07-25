from django.core.management.base import BaseCommand
from Store.models import Product, Category
from django.urls import reverse

class Command(BaseCommand):
    help = 'Runs a weekly SEO health audit for ProjectStore.pk (cPanel friendly)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Weekly SEO Health Audit..."))
        
        products = Product.objects.filter(is_active=True)
        missing_meta_desc = 0
        missing_alt_text = 0
        short_descriptions = 0
        
        for p in products:
            if not p.meta_description:
                missing_meta_desc += 1
            if not p.alt_text:
                missing_alt_text += 1
            if len(p.description or '') < 150:
                short_descriptions += 1
                
        categories = Category.objects.filter(is_active=True)
        
        self.stdout.write(self.style.SUCCESS("=== WEEKLY SEO AUDIT REPORT ==="))
        self.stdout.write(f"Total Active Products: {products.count()}")
        self.stdout.write(f"Total Active Categories: {categories.count()}")
        self.stdout.write(f"Products Missing Meta Description: {missing_meta_desc}")
        self.stdout.write(f"Products Missing Custom Alt Text (Using Fallback): {missing_alt_text}")
        self.stdout.write(f"Products With Thin Description (<150 chars): {short_descriptions}")
        
        if missing_meta_desc == 0 and short_descriptions == 0:
            self.stdout.write(self.style.SUCCESS("SEO Status: EXCELLENT - All products ready for indexing!"))
        else:
            self.stdout.write(self.style.WARNING("SEO Status: ACTION REQUIRED - Add meta descriptions for optimal CTR."))
