import json
import piexif
import os

def add_tags_to_exif(json_path):
    # 1. Load the JSON data
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    # Ensure we are handling a list of entries
    entries = data if isinstance(data, list) else [data]

    for entry in entries:
        file_path = entry.get('file_path')
        tags = entry.get('tags', [])

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        # 2. Prepare the tag string
        # XPKeywords requires a little-endian UTF-16 encoded string
        tag_string = ";".join(tags)
        xp_keywords = tag_string.encode("utf-16le")

        try:
            # 3. Load existing EXIF or create new if empty
            exif_dict = piexif.load(file_path)
            
            # 0th IFD is where XPKeywords lives (Tag ID 40094)
            exif_dict["0th"][40094] = xp_keywords
            
            # 4. Insert back into the file
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file_path)
            
            print(f"Successfully tagged: {entry['file_name']}")
            
        except Exception as e:
            print(f"Failed to process {file_path}: {e}")

if __name__ == "__main__":
    # Point this to your specific JSON file
    add_tags_to_exif('file-tags.json')