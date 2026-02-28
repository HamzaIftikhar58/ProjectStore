from PIL import Image
import os

# Paths
static_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore\static\Images"

def optimize_image(filename, target_width=None, quality=60):
    path = os.path.join(static_dir, filename)
    if not os.path.exists(path):
        # Try if it's already webp we want to re-compress
        if not path.endswith('.webp'):
            webp_path = os.path.splitext(path)[0] + ".webp"
            if os.path.exists(webp_path):
                path = webp_path
    
    if not os.path.exists(path):
        print(f"Skipping {filename}, not found.")
        return
    
    img = Image.open(path)
    
    # Resize if needed
    if target_width and img.size[0] > target_width:
        w_percent = (target_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
    
    # Save as WebP with aggressive quality
    output_path = os.path.splitext(os.path.join(static_dir, filename))[0] + ".webp"
    img.save(output_path, "WEBP", quality=quality)
    print(f"Optimized {filename} -> {output_path} (Size: {os.path.getsize(output_path)} bytes)")

# 1. Re-compress LCP Poster (EXTREME)
optimize_image("zombie_apocalypse_video_poster.jpg", quality=25)

# 2. Resize and Compress Logo (Aggressive)
optimize_image("project_store_logo.png", target_width=434, quality=40)

# 3. Optimize ISOL Logo in footer
optimize_image("wlogo.png", target_width=113, quality=40) # 113 for 2.17 ratio if height=52
