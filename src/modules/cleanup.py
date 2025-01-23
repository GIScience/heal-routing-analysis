#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small cleaning program"""


import shutil
from pathlib import Path


def cleanup_temp(data_dir):
    """Loop through ./data/ and delete temporary files no longer needed"""

    for item in list(data_dir.iterdir()):
        if item in list(data_dir.glob("*_clip*.tif")):
            item.unlink()

    temp_dir = data_dir / "temp"
    if temp_dir.exists():
        for item in list(temp_dir.iterdir()):
            if item.is_file() and item not in list(temp_dir.glob("*.osm")):
                item.unlink()

    ox_cache_path = Path("./cache")
    try:
        if ox_cache_path.exists():
            shutil.rmtree(ox_cache_path)
    except Exception as e:
        print(f"Failed to delete {ox_cache_path}. Reason: {e}")


def full_cleanup(data_dir, out_dir):
    """Cleans the project folder (deletes export folder and temp data)"""

    cleanup_temp(data_dir)

    try:
        shutil.rmtree(out_dir)
    except Exception as e:
        print(f"Failed to delete {out_dir}. Reason: {e}")
