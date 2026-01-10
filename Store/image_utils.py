from io import BytesIO
from PIL import Image, ImageEnhance
from django.core.files.base import ContentFile
from django.conf import settings
import os
import math

def add_watermark(image):
    """
    Apply a single large diagonal watermark to the image.
    """
    try:
        # Construct path to the watermark image
        watermark_path = os.path.join(settings.BASE_DIR, 'Store', 'static', 'Images', 'project_store_logo.png')
        
        if not os.path.exists(watermark_path):
            print(f"⚠️ Watermark not found at: {watermark_path}")
            return image
        
        # Open watermark
        watermark = Image.open(watermark_path).convert("RGBA")
        
        # Calculate size: We want the watermark to cover a good portion of the image diagonally
        # Let's make the watermark width about 70% of the image's diagonal size
        image_diagonal = math.sqrt(image.width**2 + image.height**2)
        w_width = int(image_diagonal * 0.7)
        
        # Maintain aspect ratio
        aspect_ratio = watermark.height / watermark.width
        w_height = int(w_width * aspect_ratio)
        
        watermark = watermark.resize((w_width, w_height), Image.Resampling.LANCZOS)
        
        # Rotate watermark
        watermark = watermark.rotate(45, expand=True, resample=Image.Resampling.BICUBIC)
        
        # Adjust transparency - keeping it visible but not overwhelming since it's large
        opacity = 0.35 
        if 'A' in watermark.getbands():
            alpha = watermark.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            watermark.putalpha(alpha)
        else:
             watermark.putalpha(int(255 * opacity))
        
        # Create overlay layer
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        overlay = Image.new('RGBA', image.size, (0,0,0,0))
        
        # Calculate center position
        # watermark has been rotated and expanded, so its size changed.
        # We want to paste it such that its center matches image center.
        
        wm_w, wm_h = watermark.size
        bg_w, bg_h = image.size
        
        pos_x = (bg_w - wm_w) // 2
        pos_y = (bg_h - wm_h) // 2
        
        # Paste watermark onto overlay
        overlay.paste(watermark, (pos_x, pos_y), mask=watermark)
                
        # Composite the image and the watermark
        return Image.alpha_composite(image, overlay)
        
    except Exception as e:
        print(f"❌ Error adding watermark: {e}")
        return image

def compress_image(image_field, quality=90, max_size=(1920, 1080), format='WEBP'):
    """
    Compress, optimize, and watermark an image.
    """
    try:
        # Open the image
        img = Image.open(image_field)

        # Convert to RGBA for processing
        if img.mode != 'RGBA':
             img = img.convert('RGBA')

        # Resize while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # APPPLY WATERMARK
        img = add_watermark(img)

        output = BytesIO()

        # Save as WebP or JPEG
        if format.upper() == 'WEBP':
            img.save(output, format='WEBP', quality=quality, method=6, lossless=False)
            ext = '.webp'
        else:
            # For JPEG, we must discard alpha
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
            img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)
            ext = '.jpg'

        compressed_data = output.getvalue()
        
        # Create a new filename with the correct extension
        filename = os.path.splitext(image_field.name)[0] + ext
        return ContentFile(compressed_data, name=filename)

    except Exception as e:
        print(f"❌ Error compressing/watermarking image: {e}")
        return None
