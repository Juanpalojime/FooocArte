
import os
import shutil
import json
import datetime

def save_to_drive(local_path, metadata, drive_root="/content/drive/MyDrive/FooocArte/outputs"):
    """
    Saves an image and updates metadata.json to Google Drive.
    Structure: drive_root/YYYY-MM-DD/batch_id/image.png
    """
    if not os.path.exists(local_path):
        print(f"[Drive] Local file not found: {local_path}")
        return None

    try:
        # 1. Determine Path
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        batch_id = metadata.get("batch_id", "manual_batch")
        
        target_dir = os.path.join(drive_root, date_str, batch_id)
        os.makedirs(target_dir, exist_ok=True)
        
        filename = os.path.basename(local_path)
        target_path = os.path.join(target_dir, filename)
        
        # 2. Copy Image
        shutil.copy2(local_path, target_path)
        
        # 3. Update Metadata JSON (Incremental Append)
        meta_file = os.path.join(target_dir, "metadata.json")
        
        current_data = []
        if os.path.exists(meta_file):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        current_data = json.loads(content)
                        if not isinstance(current_data, list):
                            current_data = [current_data]
            except Exception as e:
                print(f"[Drive] Error reading metadata.json: {e}")
                
        # Create Entry
        entry = {
            "filename": filename,
            "timestamp": datetime.datetime.now().isoformat(),
            "prompt": metadata.get("prompt", ""),
            "seed": str(metadata.get("seed", "")),
            "preset": metadata.get("preset", "None"),
            "clip_score": metadata.get("clip_score", None),
            "mode": metadata.get("mode", "unknown"),
            "input_file": metadata.get("input_file", None) # For folder mode
        }
        
        current_data.append(entry)
        
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2)
            
        print(f"[Drive] Saved {filename} to {target_dir}")
        return target_path

    except Exception as e:
        print(f"[Drive] Sync Failed: {e}")
        return None
