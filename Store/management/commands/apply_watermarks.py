from django.core.management.base import BaseCommand
from Store.models import Product, ProductImage, ProductVariant
from Store.image_utils import compress_image
from django.db.models.signals import pre_save
from Store.signals import compress_product_image, compress_product_extra_image, compress_product_variant_image
import os
import difflib
from django.conf import settings

def find_original_image(current_path_rel):
    """
    Attempts to find the original uncompressed/unwatermarked image based on size and name.
    """
    try:
        # Check if we have media root
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
                # Find larger files (originals are usually uncompressed and significantly larger)
                # We use a 1.2x multiplier as a heuristic
                if f_size > current_size * 1.2: 
                    candidates.append(f)
                    
        if not candidates:
            return None
            
        # Match based on filename similarity
        best_matches = difflib.get_close_matches(filename, candidates, n=1, cutoff=0.1)
        
        if best_matches:
            return os.path.join(directory, best_matches[0])
        
        return None
    except Exception as e:
        print(f"Error finding original: {e}")
        return None

def process_and_save(instance, image_field, stdout):
    try:
        if not image_field:
            return

        stdout.write(f"  Processing: {image_field.name}")
        
        # Try to recover original to avoid double watermark
        original_path = find_original_image(image_field.name)
        
        opened_file = None
        image_to_process = None
        
        if original_path:
            stdout.write(f"    ✅ Found original: {os.path.basename(original_path)}")
            opened_file = open(original_path, 'rb')
            image_to_process = opened_file
        else:
            stdout.write("    ⚠️ No original found. Using current (might overlay watermark).")
            image_to_process = image_field

        # Compress and Watermark
        new_image = compress_image(image_to_process)
        
        if opened_file:
            opened_file.close()

        if new_image:
            filename = os.path.basename(image_field.name)
            # Save without triggering signals
            image_field.save(filename, new_image, save=False)
            instance.save()
            # stdout.write(f"    Updated.")
            
    except Exception as e:
        stdout.write(f"    ❌ Error: {e}")

class Command(BaseCommand):
    help = 'Apply watermark to all existing images, attempting to recover originals first.'

    def handle(self, *args, **options):
        # Disconnect signals
        pre_save.disconnect(compress_product_image, sender=Product)
        pre_save.disconnect(compress_product_extra_image, sender=ProductImage)
        pre_save.disconnect(compress_product_variant_image, sender=ProductVariant)
        
        self.stdout.write("Signals disconnected. Starting intelligent bulk watermarking...")
        
        # 1. Process Main Products
        products = Product.objects.all()
        self.stdout.write(f"\nProcessing {products.count()} products...")
        for product in products:
            process_and_save(product, product.main_image, self.stdout)

        # 2. Process Variants
        variants = ProductVariant.objects.all()
        self.stdout.write(f"\nProcessing {variants.count()} variants...")
        for variant in variants:
            process_and_save(variant, variant.image, self.stdout)

        # 3. Process Gallery
        images = ProductImage.objects.all()
        self.stdout.write(f"\nProcessing {images.count()} gallery images...")
        for img in images:
            process_and_save(img, img.image, self.stdout)

        self.stdout.write(self.style.SUCCESS("\nSuccessfully processed all images."))
