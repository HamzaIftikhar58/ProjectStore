from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from .models import Product, ProductImage, ProductVariant
from .image_utils import compress_image
import os


@receiver(pre_save, sender=Product)
def compress_product_image(sender, instance, **kwargs):
    """
    Compress and optimize the main Product image before saving.
    Handles both new uploads and updates to existing images.
    """
    if not instance.main_image:
        return

    try:
        # Check if this is an update and the image has changed
        if instance.pk:
            try:
                old_instance = Product.objects.get(pk=instance.pk)
                if old_instance.main_image and old_instance.main_image != instance.main_image:
                    # Delete old image if it exists and is being replaced
                    old_instance.main_image.delete(save=False)
            except Product.DoesNotExist:
                pass

        # Compress and replace image
        compressed_image = compress_image(instance.main_image)
        if compressed_image:
            original_name = os.path.basename(instance.main_image.name)
            instance.main_image.save(original_name, compressed_image, save=False)

    except Exception as e:
        print(f"Error processing Product image: {e}")


@receiver(pre_save, sender=ProductImage)
def compress_product_extra_image(sender, instance, **kwargs):
    """
    Compress and optimize additional Product images before saving.
    Handles both new uploads and updates to existing images.
    """
    if not instance.image:
        return

    try:
        # Check if this is an update and the image has changed
        if instance.pk:
            try:
                old_instance = ProductImage.objects.get(pk=instance.pk)
                if old_instance.image and old_instance.image != instance.image:
                    # Delete old image if it exists and is being replaced
                    old_instance.image.delete(save=False)
            except ProductImage.DoesNotExist:
                pass

        # Compress and replace image
        compressed_image = compress_image(instance.image)
        if compressed_image:
            original_name = os.path.basename(instance.image.name)
            instance.image.save(original_name, compressed_image, save=False)

    except Exception as e:
        print(f"Error processing Product extra image: {e}")


# Add cleanup signals to delete files when objects are deleted
@receiver(pre_delete, sender=Product)
def delete_product_image(sender, instance, **kwargs):
    """Delete image files when a Product is deleted."""
    if instance.main_image and os.path.isfile(instance.main_image.path):
        instance.main_image.delete(save=False)


@receiver(pre_delete, sender=ProductImage)
def delete_product_extra_image(sender, instance, **kwargs):
    """Delete image files when a ProductImage is deleted."""
    if instance.image and os.path.isfile(instance.image.path):
        instance.image.delete(save=False)


@receiver(pre_save, sender=ProductVariant)
def compress_product_variant_image(sender, instance, **kwargs):
    """
    Compress and watermark ProductVariant images.
    """
    if not instance.image:
        return

    try:
        if instance.pk:
            try:
                old_instance = ProductVariant.objects.get(pk=instance.pk)
                if old_instance.image and old_instance.image != instance.image:
                    old_instance.image.delete(save=False)
            except ProductVariant.DoesNotExist:
                pass

        compressed_image = compress_image(instance.image)
        if compressed_image:
            original_name = os.path.basename(instance.image.name)
            instance.image.save(original_name, compressed_image, save=False)

    except Exception as e:
        print(f"Error processing ProductVariant image: {e}")


@receiver(pre_delete, sender=ProductVariant)
def delete_product_variant_image(sender, instance, **kwargs):
    """Delete image files when a ProductVariant is deleted."""
    if instance.image and os.path.isfile(instance.image.path):
        instance.image.delete(save=False)
