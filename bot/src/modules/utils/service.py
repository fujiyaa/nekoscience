


import os

def cleanup_files(*file_paths: str):
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {file_path}")
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")