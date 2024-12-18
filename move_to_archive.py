import os
import shutil
from datetime import datetime

# Files/directories to keep in root
KEEP_LIST = [
    '.git',
    '.gitignore',
    '.vscode',
    'venv',
    'src',
    'tests',
    'instance',
    'README.md',
    'LICENSE',
    'requirements.txt',
    'setup.py',
    'wsgi.py',
    '.flaskenv',
    '_archive',
    'move_to_archive.py'  # This script itself
]

def move_to_archive():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(root_dir, '_archive')
    
    # Create archive directory if it doesn't exist
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # Create a timestamp subdirectory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_subdir = os.path.join(archive_dir, f'archive_{timestamp}')
    os.makedirs(archive_subdir)
    
    # Move files and directories
    for item in os.listdir(root_dir):
        if item not in KEEP_LIST:
            src_path = os.path.join(root_dir, item)
            dst_path = os.path.join(archive_subdir, item)
            
            try:
                if os.path.exists(src_path):
                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dst_path)
                        os.remove(src_path)
                        print(f"Moved file: {item}")
                    elif os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                        shutil.rmtree(src_path)
                        print(f"Moved directory: {item}")
            except Exception as e:
                print(f"Error moving {item}: {str(e)}")

if __name__ == '__main__':
    move_to_archive()
