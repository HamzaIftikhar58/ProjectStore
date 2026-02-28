import os
import shutil

def main():
    base_dir = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore"
    static_dirs = [
        os.path.join(base_dir, "static"),
        os.path.join(base_dir, "Store", "static")
    ]
    
    ignore_exts = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.mp4'}
    
    # Collect all static files
    static_files = []
    for d in static_dirs:
        if not os.path.exists(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext not in ignore_exts:
                    static_files.append({
                        'path': os.path.join(root, f),
                        'name': f,
                        'name_no_ext': os.path.splitext(f)[0]
                    })
    
    # Collect all search files (.html, .py, .css, .js)
    search_files = []
    exclude_dirs = {'.venv', 'staticfiles', '.git', '__pycache__'}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f.endswith(('.html', '.py', '.css', '.js')):
                search_files.append(os.path.join(root, f))
                
    file_contents = []
    for sf in search_files:
        try:
            with open(sf, 'r', encoding='utf-8') as f:
                file_contents.append((sf, f.read()))
        except Exception:
            pass
            
    unused = []
    for sf_info in static_files:
        name = sf_info['name']
        path = sf_info['path']
        
        is_used = False
        for sf_path, content in file_contents:
            if sf_path == path:
                continue
            if name in content:
                is_used = True
                break
        
        if not is_used:
            unused.append(path)
            
    print(f"Total non-image static files checked: {len(static_files)}")
    print(f"Unused files found: {len(unused)}")
    
    import re
    
    # Criteria 1: 12-character hex hashes (Django collectstatic leftovers)
    hash_pattern = re.compile(r'\.[a-f0-9]{12}\.[a-z0-9]+$')
    
    deleted_count = 0
    for u in unused:
        basename = os.path.basename(u)
        
        # Determine if it should be deleted
        delete_it = False
        
        # Delete if it's a Django hashed file
        if hash_pattern.search(basename):
            delete_it = True
        # Delete if it's an unused vendor library
        elif 'vendor\\libs\\' in u:
            delete_it = True
            
        if delete_it:
            try:
                os.remove(u)
                print(f"Deleted: {u}")
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {u}: {e}")
                
    # Clean up empty directories in vendor/libs
    for d in static_dirs:
        vendor_libs_dir = os.path.join(d, 'assets', 'vendor', 'libs')
        if os.path.exists(vendor_libs_dir):
            for folder in os.listdir(vendor_libs_dir):
                folder_path = os.path.join(vendor_libs_dir, folder)
                if os.path.isdir(folder_path):
                    # Check if empty or only contains images
                    has_non_images = False
                    for root, _, files in os.walk(folder_path):
                        for f in files:
                            ext = os.path.splitext(f)[1].lower()
                            if ext not in ignore_exts:
                                has_non_images = True
                                break
                        if has_non_images:
                            break
                    
                    if not has_non_images:
                        try:
                            shutil.rmtree(folder_path)
                            print(f"Deleted empty/image-only vendor folder: {folder_path}")
                        except Exception as e:
                            pass
                            
    print(f"\nCleanup complete. Total files deleted: {deleted_count}")

if __name__ == "__main__":
    main()
