import logging
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
