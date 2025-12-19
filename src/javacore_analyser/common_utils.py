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


def add_common_args(parser):
    parser.add_argument("--separator",
                        help='Input files separator (default ";")')
    parser.add_argument("--skip_boring", help='Skips drilldown page generation for threads that do not do anything', )
    parser.add_argument("--use_ai", required=False, help="Use AI genereated analysis")
    parser.add_argument("--config_file", required=False, help="Configuration file", default="config.ini")

def add_web_args(parser):
    """
    Add web-specific command line arguments to the given parser object.

    This function is designed to be used with the argparse module to add
    command line arguments for a web application. The arguments added are:

    --debug:
        Enables debug mode. This should only be used during development.

    --port:
        Specifies the port number on which the application will run.

    --reports-dir:
        Specifies the directory where application reports will be stored.
    """
    parser.add_argument("--debug", help="Debug mode. Use only for development")
    parser.add_argument("--port", help="Port to run application")
    parser.add_argument("--reports-dir", help="Directory where app reports are stored")
