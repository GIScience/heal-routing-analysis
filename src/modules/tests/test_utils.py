#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for utils"""


from ..utils import subfolder
from pathlib import Path


def test_subfolder():
    """
    Test if folders are created correctly
    :return:
    """
    out_dir = Path("export")
    timestamp = "test_stamp"

    expected_folder_time = "export/test_stamp"
    expected_folder_normal = "export/normal"
    actual_folder_time = subfolder(out_dir, timestamp).as_posix()
    actual_folder_normal = subfolder(out_dir, "normal").as_posix()

    assert expected_folder_time == actual_folder_time
    assert expected_folder_normal == actual_folder_normal
