#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
import configparser
import logging
import os.path
import shutil

import importlib_resources


# Assisted by watsonx Code Assistant

class Properties:
    """
    A singleton class to manage properties that should not be changed after initialization.
    """

    __instance = None

    # Python doesn't have private constructors
    # The key prevents creation of an object of this class from outside the class
    __create_key = object()

    @classmethod
    def create(cls):
        return Properties(cls.__create_key)

    def __init__(self, create_key):
        # the assertion below effectively makes the constructor private
        assert (create_key == Properties.__create_key), \
            "Properties objects must be created using Properties.create"
        self.properties = {}


    def load_properties(self, args):
        """
        Reads properties from a config file and command line arguments, converting string values to Boolean or
        numbers where applicable. Args: args (argparse.Namespace): Command line arguments containing optional
        properties.
        """

        properties = {}
        config_file = args.config_file
        if not os.path.exists(config_file):
            logging.info(f"Config file {config_file} does not exist. Creating default config file")
            self._generate_default_config(config_file)

        logging.info(f"Reading properties from {config_file}")

        # Use configparser to load the properties. See more on https://docs.python.org/3/library/configparser.html
        config = configparser.ConfigParser()
        config.read(config_file)

        for section in config.sections():
            for key, value in config[section].items():
                logging.info(f"Reading property {key} with value {value}")
                properties[key] = value

        # Read properties from args and override them
        for arg in vars(args):
            arg_value = getattr(args, arg)
            if arg_value is not None:
                logging.info(f"Reading property {arg} with value {arg_value}")
                properties[arg] = arg_value

        # For each property change the type from String to Boolean or number
        for key, value in properties.items():
            if isinstance(value, str):
                if value.lower() == "true":
                    properties[key] = True
                elif value.lower() == "false":
                    properties[key] = False
                elif value.isdigit():
                    properties[key] = int(value)
        self.properties = properties

    @staticmethod
    def get_instance():
        if not Properties.__instance:
            Properties.__instance = Properties.create()
        return Properties.__instance

    def skip_boring(self):
        return self.properties["skip_boring"]

    def get_property(self, key, default_value=None):
        if key in self.properties:
            return self.properties[key]
        else:
            return default_value

    @staticmethod
    def _generate_default_config(config_file):
        with importlib_resources.path("javacore_analyser", "config.ini") as config_ini_resource:
            shutil.copy2(config_ini_resource, config_file)
