# Media Optimization Toolkit

This project includes custom Python scripts to automatically optimize video assets for the web and generate high-quality poster thumbnails. These scripts are designed to be "smart" (idempotent)—they will skip files that have already been processed.

## Prerequisites

1.  **Python 3.x**: Ensure Python is installed and added to your PATH.
2.  **FFmpeg**:
    - Must be installed on your system.
    - Verify by running `ffmpeg -version` in your terminal.
    - If the script fails to find it, update the `ffmpeg_path` variable in `optimize_videos.py` to point to your specific `ffmpeg.exe` location.
3.  **Python Libraries**:
    - You need `opencv-python` for the thumbnail generator.
    - Install it via pip:
      ```bash
      pip install opencv-python
      ```

## Included Scripts

### 1. `optimize_videos.py`

**Purpose**: Compresses videos and optimizes them for web streaming.

- **Features**:
  - Reduces file size by ~60-70% using H.264 codec.
  - Applies `+faststart` (moves metadata to the start of the file) so videos play instantly before fully downloading.
  - Removes audio tracks to save space (since background videos are usually muted).
  - **Smart Skipping**: Checks `Store/static/videos/optimized_log.txt` to avoid re-processing videos.

**Usage**:

```bash
python optimize_videos.py
```

### 2. `generate_thumbnails.py`

**Purpose**: Extracts the first frame of every video to create a static poster image.

- **Features**:
  - Scans for all `.mp4` files in `Store/static/videos`.
  - Generates a high-quality `.jpg` thumbnail in `Store/static/Images`.
  - Naming convention: `video_name.mp4` -> `video_name_poster.jpg`.
  - **Smart Skipping**: If the `_poster.jpg` already exists, it skips generation.

**Usage**:

```bash
python generate_thumbnails.py
```

## Workflow for New Videos

When you add a new video file (e.g., `new_hero_bg.mp4`) to `Store/static/videos`:

1.  **Run the Optimizer**:

    ```bash
    python optimize_videos.py
    ```

    _This will detect the new file, compress it, verify the size reduction, and log it as "done"._

2.  **Run the Thumbnail Generator**:

    ```bash
    python generate_thumbnails.py
    ```

    _This will create `new_hero_bg_poster.jpg` in your images folder._

3.  **Update Your HTML**:
    Use the new assets in your templates with the following optimized HTML structure:
    ```html
    {% load static %}
    <video
      autoplay
      muted
      loop
      playsinline
      class="your-class"
      preload="metadata"
      poster="{% static 'Images/new_hero_bg_poster.jpg' %}"
    >
      <source src="{% static 'videos/new_hero_bg.mp4' %}" type="video/mp4" />
      Your browser does not support the video tag.
    </video>
    ```

## Troubleshooting

- **"File not found"**: Ensure the paths in the scripts (`video_dir`, `image_dir`) match your project structure.
- **"cv2 module not found"**: Run `pip install opencv-python`.
- **FFmpeg errors**: Open `optimize_videos.py` and check the `ffmpeg_path` variable at the top of the file.
