#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

class Properties:

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
        self.skip_boring = True

    @staticmethod
    def get_instance():
        if not Properties.__instance:
            Properties.__instance = Properties.create()
        return Properties.__instance
