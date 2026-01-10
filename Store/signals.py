from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from .models import Product, ProductImage, ProductVariant
from .image_utils import compress_image
import os
from django.conf import settings

def save_original_backup(image_field, subfolder):
    """
    Saves a raw copy of the original image to MEDIA_ROOT/originals/<subfolder>/
    """
    try:
        if not settings.MEDIA_ROOT:
            return None

        # Create backup directory
        backup_dir = os.path.join(str(settings.MEDIA_ROOT), 'originals', subfolder)
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(image_field.name)
        backup_path = os.path.join(backup_dir, filename)
        
        # Read content from the field
        if image_field.closed:
            image_field.open()
        
        # We read into memory - be careful with very large files, but images are usually ok
        content = image_field.read()
            
        with open(backup_path, 'wb') as f:
            f.write(content)
            
        # IMPORTANT: Reset pointer so subsequent reads (like compression) work
        image_field.seek(0)
        
        return backup_path
    except Exception as e:
        print(f"⚠️ Error saving backup: {e}")
        return None

@receiver(pre_save, sender=Product)
def compress_product_image(sender, instance, **kwargs):
    """
    Handle Product main_image: Backup original, then Watermark & Rename.
    """
    if not instance.main_image:
        return

    try:
        process = False
        if not instance.pk:
            process = True
        else:
            try:
                old = Product.objects.get(pk=instance.pk)
                if old.main_image != instance.main_image:
                    process = True
                    # Optional: Cleanup old file? Only IF it was watermarked.
                    # if old.main_image: old.main_image.delete(save=False)
            except Product.DoesNotExist:
                pass
        
        if process:
            # 1. Backup Original
            save_original_backup(instance.main_image, 'products/main')
            
            # 2. Compress & Watermark
            compressed = compress_image(instance.main_image)
            
            if compressed:
                # 3. Rename with _watermarked
                name, ext = os.path.splitext(os.path.basename(compressed.name))
                if '_watermarked' not in name:
                    new_name = f"{name}_watermarked{ext}"
                else:
                    new_name = compressed.name
                
                # Replace the field content with the new watermarked file
                instance.main_image.save(new_name, compressed, save=False)
                
    except Exception as e:
        print(f"Error processing Product image: {e}")


@receiver(pre_save, sender=ProductImage)
def compress_product_extra_image(sender, instance, **kwargs):
    if not instance.image:
        return

    try:
        process = False
        if not instance.pk:
            process = True
        else:
            try:
                old = ProductImage.objects.get(pk=instance.pk)
                if old.image != instance.image:
                    process = True
            except ProductImage.DoesNotExist:
                pass
        
        if process:
            save_original_backup(instance.image, 'products/gallery')
            compressed = compress_image(instance.image)
            
            if compressed:
                name, ext = os.path.splitext(os.path.basename(compressed.name))
                if '_watermarked' not in name:
                    new_name = f"{name}_watermarked{ext}"
                else:
                    new_name = compressed.name
                    
                instance.image.save(new_name, compressed, save=False)

    except Exception as e:
        print(f"Error processing Product extra image: {e}")


@receiver(pre_save, sender=ProductVariant)
def compress_product_variant_image(sender, instance, **kwargs):
    if not instance.image:
        return

    try:
        process = False
        if not instance.pk:
            process = True
        else:
            try:
                old = ProductVariant.objects.get(pk=instance.pk)
                if old.image != instance.image:
                    process = True
            except ProductVariant.DoesNotExist:
                pass
        
        if process:
            save_original_backup(instance.image, 'products/variants')
            compressed = compress_image(instance.image)
            
            if compressed:
                name, ext = os.path.splitext(os.path.basename(compressed.name))
                if '_watermarked' not in name:
                    new_name = f"{name}_watermarked{ext}"
                else:
                    new_name = compressed.name
                    
                instance.image.save(new_name, compressed, save=False)

    except Exception as e:
        print(f"Error processing ProductVariant image: {e}")


@receiver(pre_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    if instance.main_image and os.path.isfile(instance.main_image.path):
        instance.main_image.delete(save=False)

@receiver(pre_delete, sender=ProductImage)
def delete_product_extra_image(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        instance.image.delete(save=False)

@receiver(pre_delete, sender=ProductVariant)
def delete_product_variant_image(sender, instance, **kwargs):
    if instance.image and os.path.isfile(instance.image.path):
        instance.image.delete(save=False)
