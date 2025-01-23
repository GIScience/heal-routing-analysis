#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""General utility functions"""


import logging
import yaml


def subfolder(out_dir, time_of_day):
    """
    Returns the respective folder path and creates subfolders in out_dir with times of day if not existent already
    :param out_dir: output directory
    :param time_of_day: time of day from list or default
    :param time_i: iterator going trough the time of day list
    :return: output folder name
    """
    out_folder = out_dir / time_of_day
    out_folder.mkdir(exist_ok=True)
    return out_folder


def init_logger(name, log_file_name=None):
    """
    Set up a logger instance with stream and file logger
    :return:
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S",
    )
    # Add stream handler
    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)
    # Log file handler
    if log_file_name:
        assert log_file_name.parent.exists(), "Error during logger setup: Directory of log file does not exist."
        filehandler = logging.FileHandler(filename=log_file_name)
        filehandler.setLevel(logging.INFO)
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)
    return logger


def load_config(config_file, ors_config_file, developer_config_file):
    """
    Load config files
    :return:
    """
    assert config_file.exists(), f"Configuration file does not exist: {config_file.absolute()}"
    with open(config_file, "r") as src:
        config = yaml.safe_load(src)
    assert ors_config_file.exists(), f"ORS configuration file does not exist: {ors_config_file.absolute()}"
    with open(ors_config_file, "r") as src:
        ors_config = yaml.safe_load(src)
    assert (
        developer_config_file.exists()
    ), f"Developer configuration file does not exist: {developer_config_file.absolute()}"
    with open(developer_config_file, "r") as src:
        developer_config = yaml.safe_load(src)

    return config, ors_config, developer_config
