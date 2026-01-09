from django.core.management.base import BaseCommand
from Store.models import Product, ProductImage, ProductVariant
from Store.image_utils import compress_image
from django.db.models.signals import pre_save
from Store.signals import compress_product_image, compress_product_extra_image, compress_product_variant_image
import os
import difflib
from django.conf import settings

def find_original_image(current_path_rel):
    try:
        if not settings.MEDIA_ROOT:
            return None
            
        full_path = os.path.join(str(settings.MEDIA_ROOT), str(current_path_rel))
        if not os.path.exists(full_path):
            return None
        
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        current_size = os.path.getsize(full_path)
        
        candidates = []
        if os.path.exists(directory):
            for f in os.listdir(directory):
                f_path = os.path.join(directory, f)
                if not os.path.isfile(f_path):
                    continue
                if f == filename:
                    continue
                    
                f_size = os.path.getsize(f_path)
                # Find larger files (originals are usually uncompressed)
                if f_size > current_size * 1.2: 
                    candidates.append(f)
                    
        if not candidates:
            return None
            
        best_matches = difflib.get_close_matches(filename, candidates, n=1, cutoff=0.1)
        
        if best_matches:
            return os.path.join(directory, best_matches[0])
        
        return None
    except Exception as e:
        print(f"Error finding original: {e}")
        return None

class Command(BaseCommand):
    help = 'Test watermark on a SINGLE product with recovery'

    def handle(self, *args, **options):
        pre_save.disconnect(compress_product_image, sender=Product)
        pre_save.disconnect(compress_product_extra_image, sender=ProductImage)
        pre_save.disconnect(compress_product_variant_image, sender=ProductVariant)
        
        product = Product.objects.filter(name__icontains="AI Ambulance Detection").first()
        if not product:
            product = Product.objects.first()
            
        if not product or not product.main_image:
            self.stdout.write("No product with image found.")
            return

        self.stdout.write(f"Testing on: {product.name}")
        self.stdout.write(f"Current: {product.main_image.name}")
        
        original_path = find_original_image(product.main_image.name)
        
        image_to_process = None
        opened_file = None
        
        if original_path:
            self.stdout.write(self.style.SUCCESS(f"✅ Found original: {os.path.basename(original_path)}"))
            opened_file = open(original_path, 'rb')
            image_to_process = opened_file
        else:
            self.stdout.write(self.style.WARNING("⚠️ No original found. Using current."))
            image_to_process = product.main_image

        try:
            new_image = compress_image(image_to_process)
            
            if new_image:
                filename = os.path.basename(product.main_image.name)
                product.main_image.save(filename, new_image, save=False)
                product.save()
                self.stdout.write(self.style.SUCCESS(f"Updated {product.name}."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
        finally:
            if opened_file:
                opened_file.close()
