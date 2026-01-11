import os
import subprocess
import shutil
import glob

ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
video_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore\Store\static\videos"
log_path = os.path.join(video_dir, "optimized_log.txt")

# Read processed log
processed_files = set()
if os.path.exists(log_path):
    with open(log_path, 'r') as f:
        processed_files = set(line.strip() for line in f if line.strip())

# Scan for mp4 files
video_files = glob.glob(os.path.join(video_dir, "*.mp4"))

if not video_files:
    print("No .mp4 videos found.")

for input_path in video_files:
    filename = os.path.basename(input_path)
    
    if filename in processed_files:
        print(f"Skipping {filename}: Already optimized (checked log).")
        continue
        
    temp_output = os.path.join(video_dir, f"temp_{filename}")
    
    print(f"Optimizing {filename}...")
    
    # Command for web optimization: H.264, AAC (or none), Faststart
    cmd = [
        ffmpeg_path,
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "26",
        "-preset", "faster",
        "-movflags", "+faststart", 
        "-an", # Removing audio stream
        "-y", 
        temp_output
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"Successfully optimized {filename}")
            
            # Check sizes to see savings
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(temp_output)
            print(f"Size change: {original_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB")
            
            # Replace original
            shutil.move(temp_output, input_path)
            
            # Update log
            with open(log_path, 'a') as f:
                f.write(filename + "\n")
                
        else:
            print(f"Error optimizing {filename}:")
            print(result.stderr)
            if os.path.exists(temp_output):
                os.remove(temp_output)
                
    except Exception as e:
        print(f"Exception for {filename}: {str(e)}")

print("Optimization process complete.")
