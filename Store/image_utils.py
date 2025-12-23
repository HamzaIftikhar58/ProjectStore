from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import os

def compress_image(image_field, quality=85, max_size=(1920, 1080), format='WEBP'):
    """
    Compress and optimize an image while maintaining aspect ratio.
    Prints original and compressed size for debugging.
    """
    try:
        # ✅ Print original size before compression
        try:
            original_size = image_field.size  # size in bytes
            print(f"📷 Original size: {round(original_size / 1024, 2)} KB")
        except Exception:
            print("⚠️ Could not read original image size.")

        # Open the image
        img = Image.open(image_field)

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = background

        # Resize while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = BytesIO()

        # Save as WebP or JPEG
        if format.upper() == 'WEBP':
            img.save(output, format='WEBP', quality=quality, method=6, lossless=False)
            ext = '.webp'
        else:
            img = img.convert('RGB')
            img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)
            ext = '.jpg'

        compressed_data = output.getvalue()
        compressed_size = len(compressed_data)

        # ✅ Print compressed size
        print(f"✅ Compressed size: {round(compressed_size / 1024, 2)} KB")
        if 'original_size' in locals():
            reduction = (1 - (compressed_size / original_size)) * 100
            print(f"📉 Size reduced by: {round(reduction, 2)}%")

        # Create a new filename with the correct extension
        filename = os.path.splitext(image_field.name)[0] + ext
        return ContentFile(compressed_data, name=filename)

    except Exception as e:
        print(f"❌ Error compressing image: {e}")
        return None
