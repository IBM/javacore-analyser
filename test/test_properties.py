import unittest

from javacore_analyser.Properties import Properties


class TestProperties(unittest.TestCase):

    def test_get_instance(self):
        instance = Properties.get_instance()
        self.assertIsNotNone(instance, "Properties instance should not be None")

    def test_init(self):
        # it should not be possible to create an object by calling the constructor
        properties = None
        try:
            properties = Properties()
        except Exception as ex:
            pass
        self.assertIsNone(properties, "it should not be possible to create an object by calling the constructor")
