import cv2
import os
import glob

video_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore\Store\static\videos"
image_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore\Store\static\Images"

# Scan for all mp4 files
video_files = glob.glob(os.path.join(video_dir, "*.mp4"))

if not video_files:
    print("No .mp4 files found in video directory.")

for vid_path in video_files:
    filename = os.path.basename(vid_path)
    poster_name = filename.replace(".mp4", "_poster.jpg")
    poster_path = os.path.join(image_dir, poster_name)

    if os.path.exists(poster_path):
        print(f"Skipping {filename}: Thumbnail already exists.")
        continue

    print(f"Generating thumbnail for {filename}...")
    cap = cv2.VideoCapture(vid_path)
    if not cap.isOpened():
        print(f"Failed to open {filename}")
        continue
    
    # Read the first frame
    ret, frame = cap.read()
    if ret:
        # Use high quality jpeg
        cv2.imwrite(poster_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        print(f"Created poster: {poster_name}")
    else:
        print(f"Failed to read frame from {filename}")
    
    cap.release()

print("Thumbnail generation check complete.")
