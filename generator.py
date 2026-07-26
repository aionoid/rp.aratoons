#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository generator for AraToons Kodi addon repository.

Scans all folders containing addon.xml, creates ZIP packages in zips/,
and generates addons.xml + addons.xml.md5.

Usage:
    python3 generator.py
"""

import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET


# Files/directories to exclude from ZIP packages
EXCLUDE_PATTERNS = {
    '.git', '.gitignore', '.hermes.md', '__pycache__', '.pyc', '.pyo',
    '.vscode', '.idea', 'node_modules', '.DS_Store', 'Thumbs.db',
    'generator.py', 'README.md', 'CHANGELOG.md', '.gitattributes',
    'cookie.json',  # Sensitive - contains session tokens
}


def should_exclude(filepath, folder):
    """Check if a file should be excluded from the ZIP."""
    rel = os.path.relpath(filepath, folder)
    parts = rel.split(os.sep)
    for part in parts:
        if part in EXCLUDE_PATTERNS:
            return True
    return False


def create_zip(folder, addon_id, version, zips_path):
    """Create a ZIP package for an addon."""
    addon_zip_dir = os.path.join(zips_path, addon_id)
    os.makedirs(addon_zip_dir, exist_ok=True)

    zip_filename = f"{addon_id}-{version}.zip"
    zip_filepath = os.path.join(addon_zip_dir, zip_filename)

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root_dir, dirs, files in os.walk(folder):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS]
            for file in files:
                full_path = os.path.join(root_dir, file)
                if should_exclude(full_path, folder):
                    continue
                arcname = os.path.relpath(full_path, '.')
                zip_file.write(full_path, arcname)

    print(f"  ZIP {zip_filename} ({os.path.getsize(zip_filepath)} bytes)")
    return zip_filepath


def generate_repo():
    """Generate addons.xml, addons.xml.md5, and ZIP packages."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    zips_path = os.path.join(repo_dir, 'zips')
    os.makedirs(zips_path, exist_ok=True)

    # Start building addons.xml
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    # Scan for folders containing addon.xml
    for folder in sorted(os.listdir(repo_dir)):
        xml_path = os.path.join(repo_dir, folder, 'addon.xml')
        if not os.path.isdir(folder) or not os.path.exists(xml_path):
            continue
        if folder == 'zips':
            continue

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            addon_id = root.attrib['id']
            version = root.attrib['version']

            print(f"Processing {folder} ({addon_id} v{version})...")

            # Create ZIP package
            create_zip(os.path.join(repo_dir, folder), addon_id, version, zips_path)

            # Read addon.xml content for master file (skip XML declaration)
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_lines = f.readlines()
                if xml_lines[0].startswith('<?xml'):
                    xml_lines = xml_lines[1:]
                addons_xml += ''.join(xml_lines) + '\n'

        except Exception as e:
            print(f"  ERROR processing {folder}: {e}")

    addons_xml += '</addons>\n'

    # Write addons.xml
    addons_xml_path = os.path.join(zips_path, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8') as f:
        f.write(addons_xml)

    # Write addons.xml.md5
    md5_hash = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    md5_path = os.path.join(zips_path, 'addons.xml.md5')
    with open(md5_path, 'w', encoding='utf-8') as f:
        f.write(md5_hash)

    print(f"\nGenerated {addons_xml_path}")
    print(f"Generated {md5_path}")
    print(f"MD5: {md5_hash}")


if __name__ == '__main__':
    print('Generating Kodi repository...')
    generate_repo()
    print('Done.')
