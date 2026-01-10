from django.core.management.base import BaseCommand
import os
import shutil
import subprocess
from django.conf import settings

class Command(BaseCommand):
    help = 'Optimize static videos using FFMPEG (Requires FFMPEG installed).'

    def handle(self, *args, **options):
        # Define paths
        static_video_dir = os.path.join(settings.BASE_DIR, 'Store', 'static', 'videos')
        originals_dir = os.path.join(static_video_dir, 'originals')
        
        if not os.path.exists(static_video_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {static_video_dir}"))
            return

        # Check FFMPEG
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.stdout.write(self.style.ERROR("❌ FFMPEG is not installed or not in PATH. Please install FFMPEG to optimize videos."))
            self.stdout.write("Download from: https://ffmpeg.org/download.html")
            return

        os.makedirs(originals_dir, exist_ok=True)
        
        videos = [f for f in os.listdir(static_video_dir) if f.lower().endswith(('.mp4', '.mov', '.avi'))]
        
        self.stdout.write(f"Found {len(videos)} videos to process.")
        
        for video in videos:
            input_path = os.path.join(static_video_dir, video)
            
            # Skip if it looks like an optimized file or if inside originals
            if os.path.isdir(input_path): continue
            
            self.stdout.write(f"Processing: {video}")
            
            # Backup
            backup_path = os.path.join(originals_dir, video)
            if not os.path.exists(backup_path):
                shutil.copy2(input_path, backup_path)
                self.stdout.write(f"  📦 Backed up to static/videos/originals/")
            
            # Optimize
            # We create a temporary output file
            temp_output = os.path.join(static_video_dir, f"optimized_{video}")
            
            # FFMPEG Command: H.264, AAC, CRF 28 (Good compression), Faststart for web
            cmd = [
                'ffmpeg', '-y', 
                '-i', input_path,
                '-vcodec', 'libx264', 
                '-crf', '28', 
                '-preset', 'fast',
                '-acodec', 'aac', 
                '-b:a', '128k',
                '-movflags', '+faststart',
                temp_output
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Check if size reduced
                original_size = os.path.getsize(input_path)
                new_size = os.path.getsize(temp_output)
                
                if new_size < original_size:
                    reduction = (1 - (new_size / original_size)) * 100
                    self.stdout.write(self.style.SUCCESS(f"  ✨ Optimized! Reduced by {reduction:.1f}% ({original_size/1024/1024:.1f}MB -> {new_size/1024/1024:.1f}MB)"))
                    
                    # Replace original with optimized
                    shutil.move(temp_output, input_path)
                else:
                    self.stdout.write(f"  ⚠️ Optimized file was larger. Keeping original.")
                    os.remove(temp_output)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error optimizing {video}: {e}"))
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                    
        self.stdout.write(self.style.SUCCESS("Video optimization complete."))
