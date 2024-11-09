#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import logging
import sys
from pathlib import Path

LOGGING_FORMAT = '%(asctime)s [thread: %(thread)d][%(levelname)s][%(filename)s:%(lineno)s] %(message)s'


def create_file_logging(logging_file_dir):
    logging_file = logging_file_dir + "/wait2-debug.log"
    Path(logging_file_dir).mkdir(parents=True, exist_ok=True)  # Sometimes the folder of logging might not exist
    file_handler = logging.FileHandler(logging_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logging.getLogger().addHandler(file_handler)


def create_console_logging():
    logging.getLogger().setLevel(logging.NOTSET)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logging.getLogger().addHandler(console_handler)
