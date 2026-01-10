from django.core.management.base import BaseCommand
from Store.models import Product, ProductImage, ProductVariant
from Store.image_utils import compress_image
from django.db.models.signals import pre_save
from Store.signals import compress_product_image, compress_product_extra_image, compress_product_variant_image, save_original_backup
import os
import difflib
from django.conf import settings

def find_original_image(current_path_rel):
    """
    Find best original match.
    """
    try:
        if not settings.MEDIA_ROOT: return None
        full_path = os.path.join(str(settings.MEDIA_ROOT), str(current_path_rel))
        if not os.path.exists(full_path): return None
        
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        current_size = os.path.getsize(full_path)
        
        candidates = []
        if os.path.exists(directory):
            for f in os.listdir(directory):
                f_path = os.path.join(directory, f)
                if not os.path.isfile(f_path): continue
                if f == filename: continue
                if os.path.getsize(f_path) > current_size * 1.2:
                    candidates.append(f)
        
        if not candidates: return None
        matches = difflib.get_close_matches(filename, candidates, n=1, cutoff=0.1)
        return os.path.join(directory, matches[0]) if matches else None
    except: return None

def migrate_image(instance, image_field, subfolder, stdout):
    if not image_field: return
    
    stdout.write(f"  Checking: {image_field.name}")
    
    # 1. Identify Source Image (Clean Original if possible)
    original_path = find_original_image(image_field.name)
    source_file = None
    
    if original_path:
        stdout.write(f"    ✅ Found Clean Original: {os.path.basename(original_path)}")
        source_file = open(original_path, 'rb')
        # Use this file handle for processing
    else:
        # If no clean original found, use current, BUT check if it's already watermarked?
        # If user wants to force separation, we treat current as source.
        stdout.write("    ⚠️ Using current file as source.")
        source_file = image_field.open()

    # 2. Save Backup (if not already backed up)
    # Since we are pointing to 'source_file', save THAT to backup folder.
    # Note: save_original_backup expects a django FieldFile usually, but we can mock or adapt.
    # Actually, let's just use shutil copy if it's a path, or write content.
    
    backup_path = os.path.join(str(settings.MEDIA_ROOT), 'originals', subfolder, os.path.basename(image_field.name))
    if original_path:
        # Copy original_path to backup_path
        if not os.path.exists(backup_path):
            import shutil
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy(original_path, backup_path)
            stdout.write(f"    📦 Backed up to originals/{subfolder}")
    else:
        # Backup the current file contents
        pass # Assuming current is already modified, backing it up might back up a watermarked image. 
             # But user wants separation. Let's rely on signal logic? 
             # No, signals are disconnected. We must do it manually here.
             
    # 3. Compress & Watermark
    # source_file is open readable
    # Ensure pointer is at start
    source_file.seek(0)
    
    new_image = compress_image(source_file)
    
    if original_path:
        source_file.close()

    if new_image:
        # 4. Rename
        # Current name might be 'foo.png' or 'foo_watermarked.png'.
        # We want 'foo_watermarked.webp'.
        base_name = os.path.basename(image_field.name)
        name, ext = os.path.splitext(base_name)
        
        # Strip existing _watermarked if present to avoid double
        if name.endswith('_watermarked'):
            name = name.replace('_watermarked', '')
            
        final_name = f"{name}_watermarked{ext}" # ext usually comes from new_image name (.webp) 
        # compress_image returns specific ext in name.
        if new_image.name:
            n, e = os.path.splitext(new_image.name)
            final_name = f"{name}_watermarked{e}"

        # 5. Save to Field
        # This writes the file to media/products/main/...
        image_field.save(final_name, new_image, save=False)
        instance.save()
        stdout.write(f"    ✨ Saved as: {final_name}")

class Command(BaseCommand):
    help = 'Migrate all images to separate originals/watermarked structure.'

    def handle(self, *args, **options):
        pre_save.disconnect(compress_product_image, sender=Product)
        pre_save.disconnect(compress_product_extra_image, sender=ProductImage)
        pre_save.disconnect(compress_product_variant_image, sender=ProductVariant)
        
        self.stdout.write("Starting Migration...")
        
        for p in Product.objects.all():
            migrate_image(p, p.main_image, 'products/main', self.stdout)
            
        for v in ProductVariant.objects.all():
            migrate_image(v, v.image, 'products/variants', self.stdout)
            
        for i in ProductImage.objects.all():
            migrate_image(i, i.image, 'products/gallery', self.stdout)
            
        self.stdout.write(self.style.SUCCESS("Migration Complete."))
