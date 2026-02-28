import os
from PIL import Image

def optimize_image(input_path, output_path, max_size=None):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (WebP supports RGBA too, so mostly for JPEGs)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            # Resize if a max size is provided
            if max_size:
                # Use thumbnail to preserve aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"Resized {os.path.basename(input_path)} to {img.size}")

            # Save as WebP
            img.save(output_path, "WEBP", quality=85)
            
            orig_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            saved = orig_size - new_size
            print(f"Optimized: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            print(f"  Original size: {orig_size / 1024:.1f} KB")
            print(f"  New size:      {new_size / 1024:.1f} KB")
            print(f"  Saved:         {saved / 1024:.1f} KB ({saved/orig_size*100:.1f}%)")

    except Exception as e:
        print(f"Error processing {input_path}: {e}")


def main():
    base_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore"
    img_dir = os.path.join(base_dir, "static", "Images")

    # Image mapping: (filename, max_size_tuple)
    # Sizes are generally 2x the displayed size for retina support
    images_to_optimize = {
        "zombie_apocalypse_video_poster.jpg": (723, 310),
        "project_store_logo.png": (434, 120),
        "wlogo.png": (130, 60),
        "software.png": (90, 90),
        "robot.png": (90, 90),
        "settings.png": (90, 90),
        "computer.png": (90, 90),
    }

    for filename, max_size in images_to_optimize.items():
        input_path = os.path.join(img_dir, filename)
        
        # Output will be e.g. wlogo.webp
        name_no_ext = os.path.splitext(filename)[0]
        output_filename = f"{name_no_ext}.webp"
        output_path = os.path.join(img_dir, output_filename)
        
        optimize_image(input_path, output_path, max_size)

if __name__ == "__main__":
    main()
