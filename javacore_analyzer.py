#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import argparse
import fnmatch
import locale
import logging
import os.path
import shutil
import sys
import tarfile
import traceback
import zipfile

import py7zr

from constants import DEFAULT_FILE_DELIMITER, DATA_OUTPUT_SUBDIR
from javacore_set import JavacoreSet

LOGGING_FORMAT = '%(asctime)s [%(levelname)s][%(filename)s:%(lineno)s] %(message)s'


def create_output_files_structure(output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    data_dir = output_dir + '/data'
    if os.path.isdir(data_dir):
        shutil.rmtree(data_dir, ignore_errors=True)
    logging.info("Data dir: " + data_dir)
    shutil.copytree("data", data_dir, dirs_exist_ok=True)


def create_file_logging(output_param):
    logging_file = output_param + "/wait2-debug.log"
    file_handler = logging.FileHandler(logging_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logging.getLogger().addHandler(file_handler)


def extract_archive(input_param, output_param):
    """

    Extract javacores from zip file to output_param/data

    @param input_param: Javacores zip file
    @param output_param: the location of the output of wait tool
    @return: The location of extracted javacores (output_param/data)
    """
    if input_param.endswith(".zip"):
        logging.info("Processing zip file")
        file = zipfile.ZipFile(input_param)
    elif input_param.endswith("tar.gz") or input_param.endswith(".tgz"):
        logging.info("Processing tar gz file")
        file = tarfile.open(input_param)
    elif input_param.endswith("tar.bz2"):
        file = tarfile.open(input_param)
        logging.info("Processing bz2 file")
    elif input_param.endswith(".lzma"):
        file = tarfile.open(input_param)
        logging.info("Processing lzma file")
    elif input_param.endswith(".7z"):
        file = py7zr.SevenZipFile(input_param)
        logging.info("Processing 7z file")
    else:
        logging.error("The format of file is not supported. "
                      "Currently we support only zip, tar.gz, tgz, tar.bz2 and 7z. "
                      "Cannot proceed. Exiting")
        exit(13)

    path = os.path.abspath(input_param)
    output_dir = output_param
    output_javacore_dir = output_dir + os.sep + 'data' + os.sep
    assert isinstance(output_dir, str)

    file.extractall(path=output_javacore_dir)
    file.close()

    return output_javacore_dir


def main():
    logging.getLogger().setLevel(logging.NOTSET)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logging.getLogger().addHandler(console_handler)
    logging.info("Wait2 tool")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())

    parser = argparse.ArgumentParser()
    parser.add_argument("input_param", help="Input file(s) or directory")
    parser.add_argument("output_param", help="Report output directory")
    parser.add_argument("--separator",
                        help='Input files separator (default "' + DEFAULT_FILE_DELIMITER + '"',
                        default=DEFAULT_FILE_DELIMITER)
    args = parser.parse_args()

    input_param = args.input_param
    output_param = args.output_param
    files_separator = args.separator

    try:
        logging.info("Input parameter: " + input_param)
        logging.info("Report directory: " + output_param)

        create_output_files_structure(output_param)

        # Needs to be created once output file structure is ready.
        create_file_logging(output_param)

        # Check whether as input we got list of files or single file
        # Colon is separation mark for list of input files
        if files_separator in input_param or fnmatch.fnmatch(input_param, '*javacore*.txt'):
            # Process list of the files (copy all or them to output dir
            files = input_param.split(files_separator)
            for file in files:
                file = file.strip()
                shutil.copy2(file, output_param + DATA_OUTPUT_SUBDIR)
            path = output_param
        elif os.path.isdir(input_param):
            path = input_param
        elif os.path.isfile(input_param):
            path = extract_archive(input_param, output_param)  # Extract archive to output dir
        else:
            logging.error(
                "The specified parameter " + input_param + " is not a file or a directory. Cannot process it. Exiting")
            exit(13)
        JavacoreSet.process_javacores_dir(path, output_param)
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        logging.error("Processing was not successful. Correct the problem and try again. Exiting with error 13",
                      exc_info=True)
        exit(13)


if __name__ == "__main__":
    main()
