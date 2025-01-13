#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import logging
import ntpath
from datetime import datetime
from xml.dom.minidom import Element, parseString

from tqdm import tqdm

ROOT_CLOSING_TAG = "</verbosegc>"
GC_START = "gc-start"
GC_END = "gc-end"
MEM_INFO = "mem-info"
FREE = "free"
FREE_BEFORE = "free-before"
FREE_AFTER = "free-after"
FREED = "freed"
TIMESTAMP = "timestamp"
DURATION = "durationms"
GC_COLLECTION = "gc-collection"
GC_COLLECTIONS = "gc-collections"


class VerboseGcParser:

    def __init__(self):
        self.__file_paths = []
        self.__files = []
        self.__collects = []

    def get_file_paths(self):
        return self.__file_paths

    def get_files(self):
        return self.__files

    def get_collects(self):
        return self.__collects

    def add_file(self, file):
        self.__file_paths.append(file)

    def parse_files(self, start_time, stop_time):
        logging.info("Started parsing GC files")
        for file_path in tqdm(self.__file_paths, desc="Parsing verbose gc", unit=" file"):
            try:
                collects_from_time_range = 0
                file = VerboseGcFile(file_path)
                self.__files.append(file)
                collects = file.get_collects()
                for collect in collects:
                    time = collect.get_start_time()
                    if start_time <= time <= stop_time:
                        self.__collects.append(collect)
                        collects_from_time_range += 1
                file.set_number_of_collects(collects_from_time_range)
            except GcVerboseProcessingException as ex:
                logging.warning(file_path + " was omitted due to error", ex)
        logging.info("Finished parsing GC files")

    def get_xml(self, doc):
        element = doc.createElement(GC_COLLECTIONS)
        for gcc in self.__collects:
            element.appendChild(gcc.get_xml(doc))
        return element


class GcCollection:

    def __init__(self):
        self.free_before = 0
        self.free_after = 0
        self.start_time_str = None
        self.__start_time = None
        self.duration = 0

    def freed(self):
        return int(self.free_after) - int(self.free_before)

    def get_start_time(self):
        if not self.__start_time:
            # example format: 2023-04-25T11:04:13.857
            self.__start_time = datetime.strptime(self.start_time_str, '%Y-%m-%dT%H:%M:%S.%f')
        return self.__start_time

    def display(self):
        logging.debug("start time:", self.get_start_time(), "duration", self.duration, "freed:", self.freed(), "bytes")

    def get_xml(self, doc):
        element = doc.createElement(GC_COLLECTION)
        element.setAttribute(TIMESTAMP, self.start_time_str)
        element.setAttribute(DURATION, self.duration)
        element.setAttribute(FREE_BEFORE, self.free_before)
        element.setAttribute(FREE_AFTER, self.free_after)
        element.setAttribute(FREED, str(self.freed()))
        return element


class VerboseGcFile:

    def __init__(self, path):
        self.__path = path
        self.__doc = None
        self.__root = None
        self.__number_of_collects = 0
        self.__total_number_of_collects = -1
        self.__parse()

    def __parse(self):
        # read in the file as collection of lines
        file = None
        try:
            xml_text = ""
            root_closing_tag_available = False
            file = open(self.__path, 'r+')
            lines = file.readlines()
            # find the last non-empty line
            for line in lines:
                line = line.strip()
                # workaround for https://github.com/eclipse-openj9/openj9/issues/17978
                line = line.replace("&#x1;", "?")
                xml_text = xml_text + line
                if line == ROOT_CLOSING_TAG: root_closing_tag_available = True

            if not root_closing_tag_available:
                xml_text = xml_text + ROOT_CLOSING_TAG
                logging.debug("adding closing tag")

            self.__doc = parseString(xml_text)
            self.__root = self.__doc.documentElement
        except Exception as ex:
            raise GcVerboseProcessingException() from ex
        finally:
            if not file.closed: file.close()

    def get_file_name(self):
        head, tail = ntpath.split(self.__path)
        return tail or ntpath.basename(head)

    '''
    gets the number of gc collections in this VerboseGcFile
    that occur in the time frame defined by the first and last javacore time.
    '''

    def get_number_of_collects(self):
        return self.__number_of_collects

    def set_number_of_collects(self, number):
        self.__number_of_collects = number

    '''
    gets the total number of gc collections in this VerboseGcFile
    regardless of the time when tey occurred with regards to the javacores
    '''
    def get_total_number_of_collects(self):
        if self.__total_number_of_collects < 0:
            self.get_collects()
        if self.__total_number_of_collects < 0:
            self.__total_number_of_collects = 0
        return self.__total_number_of_collects

    def get_collects(self):
        collects = []
        self.__total_number_of_collects = 0
        children = self.__root.childNodes
        i = 0
        while i < len(self.__root.childNodes):
            child = children[i]
            i += 1
            if child.__class__ is not Element: continue
            if child.tagName == GC_START:
                try:
                    self.__total_number_of_collects += 1
                    start_tag = child
                    collect = GcCollection()
                    collect.start_time_str = start_tag.getAttribute(TIMESTAMP)
                    mem_info = start_tag.getElementsByTagName(MEM_INFO)[0]
                    collect.free_before = mem_info.getAttribute(FREE)
                    end_tag = None
                    while end_tag is None and i < len(children):
                        child = children[i]
                        i += 1
                        if child.__class__ is not Element: continue
                        if child.tagName == GC_START: raise GcVerboseCorruptedLogException()
                        if child.tagName == GC_END:
                            end_tag = child
                            collect.duration = end_tag.getAttribute(DURATION)
                            mem_info = child.getElementsByTagName(MEM_INFO)[0]
                            collect.free_after = mem_info.getAttribute(FREE)
                    collects.append(collect)
                except Exception as ex:
                    logging.error(ex)
        return collects


class GcVerboseProcessingException(Exception):
    pass


class GcVerboseCorruptedLogException(GcVerboseProcessingException):
    pass
