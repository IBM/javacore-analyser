#
# Copyright IBM Corp. 2024 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import codecs
import datetime
import logging
import os.path
import re

from javacore_analyser.constants import (
    THREAD_INFO, DATETIME, SIGINFO, ENCODING,
    XMX, XMS, XMN, GC_POLICY, COMPRESSED_REFS, NO_COMPRESSED_REFS, VERBOSE_GC, UNKNOWN,
)
from javacore_analyser.thread_snapshot import ThreadSnapshot


class CorruptedJavacoreException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Javacore:

    def __init__(self):
        self.datetime = None
        self.filename = None
        self.timestamp = None
        self.snapshots = []
        self.javacore_set = None
        self.siginfo = None
        self.__total_cpu = -1
        self.__load = -1
        self.__encoding = None

    def create(self, filename, javacore_set):
        self.filename = filename
        self.siginfo = self.__parse_siginfo()
        self.datetime = self.parse_javacore_date_time()
        self.timestamp = self.datetime.timestamp()
        self.snapshots = []
        self.javacore_set = javacore_set
        self.extract_thread_snapshots()

    def is_interesting(self):  # method is to be overloaded in subclasses, ignore the static warning
        return True

    def get_cpu_percentage(self):
        if self.__total_cpu == -1:
            self.__calculate_total_cpu_and_load()
        return self.__total_cpu

    def __calculate_total_cpu_and_load(self):
        self.__total_cpu = 0
        for s in self.snapshots:
            self.__total_cpu += s.get_cpu_percentage()
        self.__load = self.__total_cpu / 100
        self.__total_cpu /= int(self.javacore_set.number_of_cpus)

    def get_load(self):
        if self.__load == -1:
            self.__calculate_total_cpu_and_load()
        return self.__load

    def get_snapshot_by_name(self, name):
        for snapshot in self.snapshots:
            if snapshot.name == name: return snapshot
        return None

    def __parse_siginfo(self) -> str:
        # 1TISIGINFO     Dump Event "systhrow" (00040000)
        # Detail "java/lang/OutOfMemoryError" "Java-Heapspeicher" received
        file = codecs.open(self.filename, encoding=self.get_encoding(), errors='strict')
        try:
            result = None
            while True:
                line = file.readline()
                if not line: break
                if line.startswith(SIGINFO + " "):
                    result = line[len(SIGINFO):].strip()
                    break
        except UnicodeDecodeError as e:
            msg: str = "Unicode, decode error in file {}. Error message: {}".format(self.basefilename(), e)
            raise CorruptedJavacoreException(msg) from e
        finally:
            file.close()
        return result

    def parse_javacore_date_time(self):
        # 1TIDATETIME    Date: 2022/04/12 at 09:56:36:266
        file = codecs.open(self.filename, encoding=self.get_encoding(), errors='strict')
        datetime_object = None  # for coding good practices only
        try:
            while True:
                line = file.readline()
                if not line: break
                if line.startswith(DATETIME + " ") or line.startswith(DATETIME + "\t"):
                    line = line[len(DATETIME):].strip()
                    fmt = "Date: %Y/%m/%d at %H:%M:%S:%f"
                    datetime_object = datetime.datetime.strptime(line, fmt)
                    break
        except UnicodeDecodeError as e:
            msg: str = "Unicode, decode error in file {}. Error message: {}".format(self.basefilename(), e)
            raise CorruptedJavacoreException(msg) from e
        finally:
            file.close()
        return datetime_object

    def get_encoding(self):
        if self.__encoding:
            return self.__encoding
        # assuming cp-850 encoding as default.
        # This should never be required, as javacores are guaranteed
        # to contain encoding information
        self.__encoding = "850"
        # opening the file without specifying the encoding (which we don't know yet)
        # the encoding line is near the top of the javacore
        # so assuming everything up to that point is plain old ASCII
        file = codecs.open(self.filename, errors='strict')
        while True:
            line = file.readline()
            if not line:
                break
            if line.startswith(ENCODING):
                # Leave the default encoding if it was not defined
                # 1TICHARSET     [not available]
                if not line.__contains__("[not available]"):
                    self.__encoding = line.split(" ")[-1].strip()
                break
        file.close()
        return self.__encoding

    def encode(self, string):
        bts = str.encode(string, self.get_encoding(), 'ignore')
        for i in range(0, len(bts)):
            # fix for 'XML Syntax error PCDATA invalid char#405'
            if bts[i] < 32 and bts[i] != 9 and bts[i] != 10 and bts[i] != 13 and bts[i] != 1:
                raise CorruptedJavacoreException("Javacore " + self.filename + " is corrupted in line " + string)
        string = bts.decode('utf-8', 'ignore')
        return string

    def extract_thread_snapshots(self):
        """ creates a ThreadSnapshot object for each "3XMTHREADINFO" tag found in the javacore """
        file = codecs.open(self.filename, encoding=self.get_encoding(), errors='strict')
        line = ""
        line_num = 0
        try:
            while True:
                line = file.readline()
                line_num += 1
                if not line:
                    break
                line = self.encode(line)
                if line.startswith(THREAD_INFO):
                    line = Javacore.process_thread_name(line, file)
                    snapshot = ThreadSnapshot.create(line, file, self)
                    self.snapshots.append(snapshot)
        except Exception as e:
            msg: str = "Corrupted javacore file {} \n" \
                       "Error message: {} \n" \
                       "Line number: {} \n" \
                       "Previous line: {} \n" \
                       .format(self.basefilename(), e, str(line_num), line)
            raise CorruptedJavacoreException(msg) from e
        finally:
            file.close()

    @staticmethod
    def process_thread_name(line, file):
        count = line.count('"')
        if count == 0: return line  # anonymous native threads
        while True:
            count = line.count('"')
            if count == 1:
                next_line = file.readline()
                line = line + next_line
            else:
                return line

    def print_javacore(self):
        logging.debug("Javacore filename: " + self.filename)
        self.print_thread_snapshots()
        logging.debug("\n")

    def print_thread_snapshots(self):
        for snapshot in self.snapshots:
            logging.debug(snapshot)

    def basefilename(self):
        return os.path.basename(self.filename)

    def basefilename_without_extension(self):
        return os.path.splitext(self.basefilename())[0]

    def get_id(self):
        """Unique identifier of javacore"""
        return self.basefilename()

    # -------------------------------------------------------------------------
    # JVM config parsing helpers — write parsed values into self.javacore_set
    # -------------------------------------------------------------------------

    @staticmethod
    def parse_mem_arg(line):
        """Extract a memory argument value (e.g. 512m, 1g) from a javacore user-arg line."""
        line = line.split()[-1]  # avoid matching the '2' in tag name 2CIUSERARG
        tokens = re.findall(r"\d+[KkMmGg]?$", line)
        if len(tokens) != 1:
            return UNKNOWN
        return tokens[0]

    def parse_xmx(self, line):
        """Parse Xmx value from *line* and store it in self.javacore_set.xmx."""
        self.javacore_set.xmx = self.parse_mem_arg(line)

    def parse_xms(self, line):
        """Parse Xms value from *line* and store it in self.javacore_set.xms."""
        self.javacore_set.xms = self.parse_mem_arg(line)

    def parse_xmn(self, line):
        """Parse Xmn value from *line* and store it in self.javacore_set.xmn."""
        self.javacore_set.xmn = self.parse_mem_arg(line)

    def parse_gc_policy(self, line):
        """Parse GC policy from *line* and store it in self.javacore_set.gc_policy."""
        self.javacore_set.gc_policy = line[line.rfind(":") + 1:].strip()

    def parse_compressed_refs(self, line):
        """Parse compressed refs flag from *line* and update self.javacore_set.compressed_refs."""
        if COMPRESSED_REFS in line:
            self.javacore_set.compressed_refs = True
        if NO_COMPRESSED_REFS in line:
            self.javacore_set.compressed_refs = False

    def parse_verbose_gc(self, line):
        """Set self.javacore_set.verbose_gc = True if *line* contains the verbose:gc flag."""
        if VERBOSE_GC in line:
            self.javacore_set.verbose_gc = True

    def add_user_arg(self, line):
        """Append the JVM user arg from *line* to self.javacore_set.user_args."""
        arg = line[line.find('-'):].rstrip()
        logging.debug("User arg: " + arg)
        self.javacore_set.user_args.append(arg)

    def parse_user_args(self, line):
        """Parse all JVM user-arg fields from *line* and update self.javacore_set attributes."""
        self.add_user_arg(line)
        if XMX in line:
            self.parse_xmx(line)
        if XMS in line:
            self.parse_xms(line)
        if XMN in line:
            self.parse_xmn(line)
        if GC_POLICY in line:
            self.parse_gc_policy(line)
        if COMPRESSED_REFS in line or NO_COMPRESSED_REFS in line:
            self.parse_compressed_refs(line)
        if VERBOSE_GC in line:
            self.parse_verbose_gc(line)
