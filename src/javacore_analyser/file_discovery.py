#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import fnmatch
import logging
import os

from javacore_analyser import tips
from javacore_analyser.constants import (
    CPU_NUMBER_TAG, USER_ARGS, OS_LEVEL, ARCHITECTURE, JAVA_VERSION, STARTTIME, CMD_LINE,
    MIN_JAVACORE_SIZE
)
from javacore_analyser.har_file import HarFile
from javacore_analyser.jvm_config_parser import JvmConfigParser
from javacore_analyser.verbose_gc import VerboseGcParser


class FileDiscovery:
    """Discovers and validates input files in the given directory tree.

    Walks the supplied path and identifies javacore, verbose GC, and HAR files.
    Small or corrupt javacore files are excluded and recorded. Common JVM metadata
    is parsed from the first javacore found.
    """

    def populate_files_list(self, javacore_analyzer):
        """Populate javacore_analyzer.files and related collections.

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance whose
                ``path``, ``files``, ``excluded_javacores``, ``gc_parser``, and
                ``har_files`` attributes will be populated.
        """
        for (dirpath, dirnames, filenames) in os.walk(javacore_analyzer.path):
            for file in filenames:
                if fnmatch.fnmatch(file, '*javacore*.txt'):
                    full_path = os.path.join(dirpath, file)
                    file_size = os.path.getsize(full_path)
                    if file_size > MIN_JAVACORE_SIZE:
                        javacore_analyzer.files.append(full_path)
                        logging.info("Javacore file found: " + file)
                    else:
                        logging.info(f"Excluding javacore file {file} with size {file_size} bytes")
                        javacore_analyzer.excluded_javacores.append(
                            {"file": file,
                             "reason": tips.ExcludedJavacoresTip.SMALL_SIZE_JAVACORES.format(file, file_size)}
                        )
                if fnmatch.fnmatch(file, '*verbosegc*'):
                    javacore_analyzer.gc_parser.add_file(dirpath + os.sep + file)
                    logging.info("VerboseGC file found: " + file)
                if fnmatch.fnmatch(file, "*.har"):
                    javacore_analyzer.har_files.append(HarFile(dirpath + os.sep + file))
                    logging.info("HAR file found: " + file)

        # Sort files by name — equivalent to sorting by date when file names follow the default format
        javacore_analyzer.files.sort()

    def parse_common_data(self, javacore_analyzer, filename):
        """Extract information common to all javacores (CPUs, JVM settings, etc.).

        Args:
            javacore_analyzer: A JavacoreAnalyzer (or JavacoreSet) instance to populate.
            filename (str): Path (absolute or relative to javacore_analyzer.path) of the
                javacore file to read.
        """
        filename = os.path.join(javacore_analyzer.path, filename)
        curr_line = ""
        i = 0
        file = None
        jvm_parser = JvmConfigParser()
        try:
            file = open(filename, 'r')
            for line in file:
                i += 1
                if line.startswith(CPU_NUMBER_TAG):  # e.g. 3XHNUMCPUS       How Many       : 16
                    javacore_analyzer.number_of_cpus = line.split()[-1]
                    continue
                elif line.startswith(USER_ARGS):
                    jvm_parser.parse_user_args(line)
                    continue
                elif line.startswith(OS_LEVEL):
                    javacore_analyzer.os_level = line[line.rfind(":") + 1:].strip()
                    continue
                elif line.startswith(ARCHITECTURE):
                    javacore_analyzer.architecture = line[line.rfind(":") + 1:].strip()
                    continue
                elif line.startswith(JAVA_VERSION):
                    javacore_analyzer.java_version = line[len(JAVA_VERSION) + 1:].strip()
                    continue
                elif line.startswith(STARTTIME):
                    javacore_analyzer.jvm_start_time = line[line.find(":") + 1:].strip()
                    continue
                elif line.startswith(CMD_LINE):
                    javacore_analyzer.cmd_line = line[len(CMD_LINE) + 1:].strip()
                    continue
        except Exception as ex:
            logging.exception(ex)
            if file is not None:
                logging.error(
                    f'Error during processing file: {file.name} \n'
                    f'line number: {i} \n'
                    f'line: {curr_line}\n'
                    f'Check the exception below what happened'
                )
        finally:
            if file is not None:
                file.close()

        jvm_parser.apply_to(javacore_analyzer)
