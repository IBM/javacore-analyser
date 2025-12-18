#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import logging
import os
import tempfile
import unittest

from javacore_analyser.properties import Properties


class TestProperties(unittest.TestCase):

    def test_get_instance(self):
        instance = Properties.get_instance()
        self.assertIsNotNone(instance, "Properties instance should not be None")
        instance2 = Properties.get_instance()
        self.assertEqual(instance, instance2, "Singleton test failure")

    def test_init(self):
        # it should not be possible to create an object by calling the constructor
        properties = None
        try:
            properties = Properties()
        except TypeError as ex:
            logging.info(ex)
            pass
        self.assertIsNone(properties, "it should not be possible to create an object by calling the constructor")

    def test_load_default_properties(self):
        properties = Properties.get_instance()
        file_name = str(tempfile.gettempdir()) + "/noneexistent_test.ini"
        args = argparse.Namespace(debug="True", port=5000, reports_dir=".", config_file=file_name)
        try:
            properties.load_properties(args)
            self.assertTrue(properties.get_property("debug"), "debug should be True")
            self.assertEqual(properties.get_property("nonexistent", 5000), 5000, "Nonexistent property should be set to 1000")
            self.assertFalse(properties.get_property("skip_boring"), "Default skip_boring should be False")
        finally:
            os.remove(file_name)

    def test_load_custom_properties(self):
        properties = Properties.get_instance()
        file_name = "test/test.ini"
        with open(file_name, "w") as file:
            file.write("[SERVER]\n")
            file.write("serveraliveinterval = 45\n")
            file.write("compression = true\n")
        args = argparse.Namespace(config_file=file_name, compression = False, arg_property=True)
        properties.load_properties(args)
        self.assertEqual(properties.get_property("serveraliveinterval"), 45, "ServerAliveInterval should be 45")
        self.assertFalse(properties.get_property("compression"), "Compression should be False")
        self.assertTrue(properties.get_property("arg_property"), "arg_property should be True")

    def test_fail_when_missing_config_file(self):
        properties = Properties.get_instance()
        args = argparse.Namespace(test="nonexistent_test.ini") # Missing config_file param
        with self.assertRaises(AttributeError):
            properties.load_properties(args)



                                                 
