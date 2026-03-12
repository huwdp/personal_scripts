import os
import base64
import json
import time
import io
import random
from pathlib import Path
from PIL import Image, ImageFile, UnidentifiedImageError
import requests

# Allow Pillow to handle slightly broken JPEGs
ImageFile.LOAD_TRUNCATED_IMAGES = True

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def clean_tags(raw_output):
    content = raw_output.lower().split(":")[-1]
    return [t.strip() for t in content.split(",") if t.strip()]

def get_image_info(path):
    try:
        with Image.open(path) as img:
            return img.width, img.height, img.format
    except:
        return 0, 0, "Unknown"

def resize_and_encode(path, max_dim=1024):
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except (UnidentifiedImageError, OSError) as e:
        log_event(f"SKIPPING: {path.name} is corrupt or not an image. Error: {e}")
        return None

def get_tags(img_path, config):
    b64_data = resize_and_encode(img_path)
    if not b64_data:
        return "ERROR_CORRUPT"
    payload = {
        "model": config["model_alias"],
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": config["prompt"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
            ]
        }],
        "temperature": 0.2
    }
    for attempt in range(1, 11):
        try:
            response = requests.post(config["server_url"], json=payload, timeout=90)
            if response.status_code == 200:
                tags = response.json()['choices'][0]['message']['content'].strip()
                return tags
        except Exception as e:
            log_event(f"RETRY {attempt}: Connection error on {img_path.name}: {e}")
    return "ERROR_FAILED_AFTER_RETRIES"

def main():
    config = load_config()
    data_file = Path(config["data_file"])
    dir = Path(config["dir"])
    image_extensions = config["image_extensions"]
    # Load existing list or create new
    if data_file.exists():
        with open(data_file, 'r') as f:
            db = json.load(f)
    else:
        db = []
    # Map of already processed paths for fast lookup
    processed_paths = {entry["file_path"] for entry in db}
    files = [f for f in dir.glob("*") if f.suffix.lower() in image_extensions]
    for i, path in enumerate(files, 1):
        file_path_str = str(path)
        if file_path_str in processed_paths:
            continue
        print(f"[{i}/{len(files)}] Processing {path.name}...")
        w, h, fmt = get_image_info(path)
        raw_response = get_tags(path, config) 
        if "ERROR" in raw_response:
            print(f"Skipping {path.name} due to API error.")
            continue
        entry = {
            "file_name": path.name,
            "file_path": file_path_str,
            "dimensions": f"{w}x{h}",
            "format": fmt,
            "tags": clean_tags(raw_response),
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        db.append(entry)
        with open(f"{data_file}.tmp", 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
        os.replace(f"{data_file}.tmp", data_file)
    print(f"\nFinished! Processed {len(db)} total images.")

if __name__ == "__main__":
    main()