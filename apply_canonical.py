import os

TEMPLATES_DIR = r"c:\Users\hamza\Downloads\ProjectStore\ProjectStore\Store\templates"
CANONICAL_TAG = '  <link rel="canonical" href="https://projectstore.pk{{ request.path }}" />\n'

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if '<link rel="canonical"' in content:
        print(f"Skipping {file_path} (already has canonical tag)")
        return

    # Find the closing </head> tag case-insensitively
    head_close_idx = content.lower().find('</head>')
    
    if head_close_idx != -1:
        # Inject canonical tag just before </head>
        new_content = content[:head_close_idx] + CANONICAL_TAG + content[head_close_idx:]
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file_path}")
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")

for root, _, files in os.walk(TEMPLATES_DIR):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))
