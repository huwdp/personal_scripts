import os
import json
import hashlib
from collections import defaultdict

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_checksum(file_path, chunk_size):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def collect_files(root, allowed_extensions, exclude_folders, exclude_hidden_folders):
    files_by_name = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(root):
        # Remove excluded directories from traversal
        dirnames[:] = [
            d for d in dirnames if d not in exclude_folders
        ]
        if exclude_hidden_folders:
            # Remove excluded exclude_hidden_folders from traversal
            dirnames[:] = [
                d for d in dirnames if not d.startswith(".")
            ]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext not in allowed_extensions:
                continue
            full_path = os.path.join(dirpath, name)
            files_by_name[name].append(full_path)
    return files_by_name


def find_duplicates(files_by_name, chunk_size):
    duplicates = []
    for name, paths in files_by_name.items():
        if len(paths) < 2:
            continue
        checksum_map = defaultdict(list)
        for path in paths:
            checksum = get_checksum(path, chunk_size)
            checksum_map[checksum].append(path)
        for checksum, files in checksum_map.items():
            if len(files) > 1:
                duplicates.append((name, checksum, files))
    return duplicates


def write_report(duplicates, output_file):
    with open(output_file, "w") as f:
        if not duplicates:
            f.write("No duplicates found\n")
            return
        for name, checksum, files in duplicates:
            f.write(f"Duplicate file name: {name}\n")
            f.write(f"Checksum: {checksum}\n")
            for file in files:
                f.write(f"  {file}\n")
            f.write("\n")


def main():
    config = load_config()
    root = config["root_dir"]
    output_file = config["output_file"]
    chunk_size = config["hash_chunk_size"]
    allowed_extensions = set(ext.lower() for ext in config["allowed_extensions"])
    exclude_folders = set(config["exclude_folders"])
    exclude_hidden_folders = config["exclude_hidden_folders"]
    print("Scanning folders...")
    files_by_name = collect_files(root, allowed_extensions, exclude_folders, exclude_hidden_folders)
    print("Checking duplicates...")
    duplicates = find_duplicates(files_by_name, chunk_size)
    print("Writing report...")
    write_report(duplicates, output_file)
    print("Finished. Report written to", output_file)


if __name__ == "__main__":
    main()