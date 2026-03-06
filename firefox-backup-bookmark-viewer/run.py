#!/usr/bin/env python3
import os
import sys
import configparser
import lz4.block
import json
from datetime import datetime

def load_profiles():
    base = os.path.expanduser("~/.mozilla/firefox")
    profiles_ini = os.path.join(base, "profiles.ini")
    if not os.path.exists(profiles_ini):
        print("profiles.ini not found.")
        sys.exit(1)
    config = configparser.ConfigParser()
    config.read(profiles_ini)
    profiles = []
    for section in config.sections():
        if not section.startswith("Profile"):
            continue
        name = config.get(section, "Name", fallback="(no name)")
        path = config.get(section, "Path")
        is_relative = config.get(section, "IsRelative", fallback="1")
        if is_relative == "1":
            full_path = os.path.join(base, path)
        else:
            full_path = path
        profiles.append({
            "name": name,
            "path": full_path,
            "exists": os.path.isdir(full_path)
        })
    return profiles

def list_backups(profile_path):
    backup_dir = os.path.join(profile_path, "bookmarkbackups")
    if not os.path.isdir(backup_dir):
        return None
    files = [
        os.path.join(backup_dir, f)
        for f in os.listdir(backup_dir)
        if f.startswith("bookmarks-") and f.endswith(".jsonlz4")
    ]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files

def decompress_jsonlz4(path):
    with open(path, "rb") as f:
        raw = f.read()
    # Firefox files start with magic header: b'mozLz40\0'
    if raw[:8] != b"mozLz40\0":
        raise ValueError("Invalid Firefox bookmark backup format.")
    decompressed = lz4.block.decompress(raw[8:])
    return json.loads(decompressed.decode("utf-8"))

def export_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(data)

def extract_filename(path):
    base_name = os.path.basename(path)
    if base_name.startswith("bookmarks-") and base_name.endswith(".jsonlz4"):
        name_part = base_name[len("bookmarks-"):-len(".jsonlz4")]
        return f"bookmarks-{name_part}.json"
    return "file.json"

def main():
    profiles = load_profiles()
    if not profiles:
        print("No profiles found.")
        sys.exit(1)
    print("\nDetected Firefox Profiles:\n")
    for i, p in enumerate(profiles):
        status = "OK" if p["exists"] else "MISSING"
        print(f"{i+1}) {p['name']}")
        print(f"   Path: {p['path']}")
        print(f"   Exists: {status}")
        if p["exists"]:
            backups = list_backups(p["path"])
            if backups is None:
                print("   bookmarkbackups: NOT FOUND")
            else:
                print(f"   bookmarkbackups: {len(backups)} files")
        print()
    choice = input("Select profile number to inspect backups: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(profiles)):
        print("Invalid choice.")
        sys.exit(1)
    selected = profiles[int(choice) - 1]
    if not selected["exists"]:
        print("Selected profile directory does not exist.")
        sys.exit(1)
    backups = list_backups(selected["path"])
    if backups is None:
        print("bookmarkbackups folder not found in this profile.")
        sys.exit(1)
    if not backups:
        print("No bookmark backups found in this profile.")
        sys.exit(1)
    print("\nAvailable backups:\n")
    for i, path in enumerate(backups):
        filename = os.path.basename(path)
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"{i+1}) {filename}  ({mtime})")
    choice = input("Select Available backups to export as HTML file: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(backups)):
        print("Invalid choice.")
        sys.exit(1)
    selected = backups[int(choice) - 1]
    data = decompress_jsonlz4(selected)
    filename = extract_filename(selected)
    export_json(json.dumps(data), filename)
    print("Exported bookmarks to \"" + filename + "\"")

if __name__ == "__main__":
    main()