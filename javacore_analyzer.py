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
import tempfile
import traceback
import zipfile

import py7zr

from constants import DEFAULT_FILE_DELIMITER, DATA_OUTPUT_SUBDIR
from javacore_set import JavacoreSet

LOGGING_FORMAT = '%(asctime)s [%(levelname)s][%(filename)s:%(lineno)s] %(message)s'

SUPPORTED_ARCHIVES_FORMATS = {"zip", "gz", "tgz", "bz2", "lzma", "7z"}

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

def extract_archive(input_archive_filename, output_path):
    """

    Extract javacores from zip file to output_param/data

    @param input_archive_filename: Javacores zip file
    @param output_path: the location of the output of wait tool
    @return: The location of extracted javacores (output_param/data)
    """

    assert isinstance(output_path, str)

    if input_archive_filename.endswith(".zip"):
        logging.info("Processing zip file")
        file = zipfile.ZipFile(input_archive_filename)
    elif input_archive_filename.endswith("tar.gz") or input_archive_filename.endswith(".tgz"):
        logging.info("Processing tar gz file")
        file = tarfile.open(input_archive_filename)
    elif input_archive_filename.endswith("tar.bz2"):
        file = tarfile.open(input_archive_filename)
        logging.info("Processing bz2 file")
    elif input_archive_filename.endswith(".lzma"):
        file = tarfile.open(input_archive_filename)
        logging.info("Processing lzma file")
    elif input_archive_filename.endswith(".7z"):
        file = py7zr.SevenZipFile(input_archive_filename)
        logging.info("Processing 7z file")
    else:
        logging.error("The format of file is not supported. "
                      "Currently we support only zip, tar.gz, tgz, tar.bz2 and 7z. "
                      "Cannot proceed. Exiting")
        exit(13)

    file.extractall(path=output_path)
    file.close()

    return output_path


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

    logging.info("Input parameter: " + input_param)
    logging.info("Report directory: " + output_param)

    # Needs to be created once output file structure is ready.
    create_file_logging(output_param)

    # Check whether as input we got list of files or single file
    # Semicolon is separation mark for list of input files
    if files_separator in input_param or fnmatch.fnmatch(input_param, '*javacore*.txt'):
        # Process list of the files (copy all or them to output dir
        files = input_param.split(files_separator)
    else:
        files = [input_param]

    try:
        # Location when we store extracted archive or copied javacore files
        javacores_temp_dir = tempfile.TemporaryDirectory()
        # It is strange but sometimes the temp directory contains the content from previous run
        #javacores_temp_dir.cleanup()

        javacores_temp_dir_name = javacores_temp_dir.name

        create_output_files_structure(output_param)

        for file in files:
            #file = file.strip() # Remove leading or trailing space in file path
            if os.path.isdir(file):
                shutil.copytree(file, javacores_temp_dir_name, dirs_exist_ok=True)
            else:
                filename, extension = os.path.splitext(file)
                extension = extension[1:] # trim trailing "."
                if extension.lower() in SUPPORTED_ARCHIVES_FORMATS:
                    extract_archive(input_param, javacores_temp_dir_name)  # Extract archive to temp dir
                else:
                    shutil.copy2(file, javacores_temp_dir_name)

        JavacoreSet.process_javacores_dir(javacores_temp_dir_name, output_param)
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        logging.error("Processing was not successful. Correct the problem and try again. Exiting with error 13",
                      exc_info=True)
        exit(13)
    finally:
        javacores_temp_dir.cleanup()


if __name__ == "__main__":
    main()
