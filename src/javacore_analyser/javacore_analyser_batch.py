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

from javacore_analyser import logging_utils
from javacore_analyser.constants import DEFAULT_FILE_DELIMITER
from javacore_analyser.javacore_set import JavacoreSet

SUPPORTED_ARCHIVES_FORMATS = {"zip", "gz", "tgz", "bz2", "lzma", "7z"}


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
        raise Exception("The format of file is not supported. "
                        "Currently we support only zip, tar.gz, tgz, tar.bz2 and 7z. "
                        "Cannot proceed.")

    file.extractall(path=output_path)
    file.close()

    return output_path


def main():
    logging_utils.create_console_logging()
    logging.info("IBM Javacore analyser")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())

    parser = argparse.ArgumentParser()
    parser.add_argument("input_param", help="Input file(s) or directory")
    parser.add_argument("output_param", help="Report output directory")
    parser.add_argument("--separator",
                        help='Input files separator (default "' + DEFAULT_FILE_DELIMITER + '")',
                        default=DEFAULT_FILE_DELIMITER)
    args = parser.parse_args()

    input_param = args.input_param
    output_param = args.output_param
    files_separator = args.separator

    logging.info("Input parameter: " + input_param)
    logging.info("Report directory: " + output_param)

    # Needs to be created once output file structure is ready.
    logging_utils.create_file_logging(output_param)

    # Check whether as input we got list of files or single file
    # Semicolon is separation mark for list of input files
    if files_separator in input_param or fnmatch.fnmatch(input_param, '*javacore*.txt'):
        # Process list of the files (copy all or them to output dir
        files = input_param.split(files_separator)
    else:
        files = [input_param]

    try:
        process_javacores_and_generate_report_data(files, output_param)
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        logging.error("Processing was not successful. Correct the problem and try again. Exiting with error 13",
                      exc_info=True)
        exit(13)


# Assisted by WCA@IBM
# Latest GenAI contribution: ibm/granite-8b-code-instruct
def generate_javecore_set_data(files):
    """
    Generate JavacoreSet data from given files.

    Parameters:
    - files (list): List of file paths to process. Can be directories or individual files.

    Returns:
    - JavacoreSet: Generated JavacoreSet object containing the processed data.
    """


    try:
        # Location when we store extracted archive or copied javacores files
        javacores_temp_dir = tempfile.TemporaryDirectory()

        javacores_temp_dir_name = javacores_temp_dir.name
        for file in files:
            if os.path.isdir(file):
                shutil.copytree(file, javacores_temp_dir_name, dirs_exist_ok=True)
            else:
                filename, extension = os.path.splitext(file)
                extension = extension[1:]  # trim trailing "."
                if extension.lower() in SUPPORTED_ARCHIVES_FORMATS:
                    extract_archive(file, javacores_temp_dir_name)  # Extract archive to temp dir
                else:
                    shutil.copy2(file, javacores_temp_dir_name)
        return JavacoreSet.process_javacores(javacores_temp_dir_name)
    finally:
        javacores_temp_dir.cleanup()


# Assisted by WCA@IBM
# Latest GenAI contribution: ibm/granite-8b-code-instruct
def process_javacores_and_generate_report_data(input_files, output_dir):
    """
    Processes Java core dump files and generates report data.

    Parameters:
    input_files (list): A list of paths to Java core dump files.
    output_dir (str): The directory where the generated report data will be saved.

    Returns:
    None
    """
    javacore_set = generate_javecore_set_data(input_files)
    javacore_set.generate_report_files(output_dir)


if __name__ == "__main__":
    main()
