#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import configparser
import logging


def read_properties(args):
    properties = {}
    config_file = args.config_file
    logging.info(f"Reading properties from {config_file}")

    # Use configparser to load the properties. See more on https://docs.python.org/3/library/configparser.html
    config = configparser.ConfigParser()
    config.sections()
    config.read(config_file)

    for section in config.sections():
        for key, value in config[section].items():
            logging.info(f"Reading property {key} with value {value}")
            properties[key] = value

    # Read properties from args and override them
    for arg in vars(args):
        logging.info(f"Reading property {arg} with value {getattr(args, arg)}")
        properties[arg] = getattr(args, arg)

    # For each property change the type from String to Boolean or number
    for key, value in properties.items():
        if value.lower() == "true": properties[key] = True
        elif value.lower() == "false": properties[key] = False
        elif value.isdigit(): properties[key] = int(value)

    return properties