#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#

import io
import logging
import os.path
import shutil
import sys
import unittest
from unittest.mock import patch

from javacore_analyser import javacore_analyser_batch
from javacore_analyser.javacore import CorruptedJavacoreException


def rm_tmp_dir():
    if os.path.exists("tmp"):
        shutil.rmtree("tmp")


class TestJavacoreAnalyser(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.ziptestargs = ["javacore_analyser", "test/data/archives/javacores.zip", "tmp"]
        self.gztestargs = ["javacore_analyser", "test/data/archives/javacores.tar.gz", "tmp"]
        self.tgztestargs = ["javacore_analyser", "test/data/archives/javacores.tgz", "tmp"]
        self.bz2testargs = ["javacore_analyser", "test/data/archives/javacores.tar.bz2", "tmp"]
        self.sevenztestargs = ["javacore_analyser", "test/data/archives/javacores.7z", "tmp"]
        self.withoutjavacoresargs = ["javacore_analyser", "test/data/archives/archive_without_javacores.zip", "tmp"]
        self.javacorefilescorrupted = ["javacore_analyser", "test/data/archives/javacores-corrupted.zip", "tmp"]
        self.javacoresstartingaaa = ["javacore_analyser", "test/data/archives/javacores-starting-aaa.zip", "tmp"]
        self.javacores_with_invalid_chars = ["javacore_analyser", "test/data/archives/javacores_with_invalid_chars.zip",
                                             "tmp"]
        self.twofilesargs_default_separator = ["javacore_analyser",
                                               "test/data/javacores/javacore.20220606.114458.32888.0001.txt"
                                               ";test/data/javacores/javacore.20220606.114502.32888.0002.txt", "tmp"]
        self.twofilesargs_different_separator = ["javacore_analyser",
                                                 "test/data/javacores/javacore.20220606.114458.32888.0001.txt"
                                                 ":test/data/javacores/javacore.20220606.114502.32888.0002.txt", "tmp",
                                                 "--separator", ":"]
        self.issue129 = ["javacore_analyser", "test/data/issue129", "tmp"]
        self.expateerror = ["javacore_analyser", "test/data/verboseGcJavacores", "tmp"]
        self.threadnameswithquotes = ["javacore_analyser", "test/data/quotationMarks", "tmp"]
        rm_tmp_dir()

    def test_api(self):
        javacore_analyser_batch.process_javacores_and_generate_report_data(["test/data/archives/javacores.zip"], "tmp")
        test_failed = False
        try:
            javacore_analyser_batch.process_javacores_and_generate_report_data(["test/data/archives/javacores-corrupted.zip"],
                                                                         "tmp")
        except CorruptedJavacoreException:
            test_failed = True
        self.assertTrue(test_failed, "API on corrupted file should fail but finished successfully")
        javacore_analyser_batch.process_javacores_and_generate_report_data(
            ["test/data/javacores/javacore.20220606.114458.32888.0001.txt",
             "test/data/javacores/javacore.20220606.114502.32888.0002.txt"], "tmp")
        javacore_analyser_batch.process_javacores_and_generate_report_data(
            ["test/data/javacores"], "tmp")

        test_failed = False
        try:
            javacore_analyser_batch.process_javacores_and_generate_report_data([], "tmp")
        except RuntimeError:
            test_failed = True
        self.assertTrue(test_failed, "API on missing javacores should fail but finished successfully")

    def test_issue129(self):
        self.runMainWithParams(self.issue129)

    # This test is running application twice. Running twice requires overwriting particular directories and
    # not fail when generating already existing directories.
    def test_run_app_twice(self):
        for i in range(2):
            self.runMainWithParams(self.ziptestargs)

    def test_quotation_marks(self):
        self.runMainWithParams(self.threadnameswithquotes)

    def test_run_zip(self):
        self.runMainWithParams(self.ziptestargs)

    def test_expat_error(self):
        os.chmod(self.expateerror[1], 0o555)
        self.runMainWithParams(self.expateerror)

    def test_run_tar_gz(self):
        self.runMainWithParams(self.gztestargs)

    def test_run_tgz(self):
        self.runMainWithParams(self.tgztestargs)

    def test_run_tar_bz2(self):
        self.runMainWithParams(self.bz2testargs)

    def test_run_7z(self):
        self.runMainWithParams(self.sevenztestargs)

    def test_process_files_not_begining_with_javacore_name(self):
        self.runMainWithParams(self.javacoresstartingaaa)

    def test_run_two_javacores(self):
        self.runMainWithParams(self.twofilesargs_default_separator)

    def test_run_two_javacores_custom_separator(self):
        self.runMainWithParams(self.twofilesargs_different_separator)

    def test_error_for_archive_without_javacores(self):
        # Run with params from https://stackoverflow.com/questions/18668947/how-do-i-set-sys-argv-so-i-can-unit-test-it
        # Redirect console from https://stackoverflow.com/questions/33767627/python-write-unittest-for-console-print
        default_output = sys.stdout
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.
        try:
            with patch.object(sys, 'argv', self.withoutjavacoresargs):
                javacore_analyser_batch.main()
        except SystemExit:
            console_output = captured_output.getvalue()
            self.assertRegex(console_output,
                             "No javacores found.")
        finally:
            sys.stdout = default_output  # Reset redirect.

    def test_javacores_with_invalid_chars(self):
        default_output = sys.stdout
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.
        try:
            with patch.object(sys, 'argv', self.javacores_with_invalid_chars):
                javacore_analyser_batch.main()
        except SystemExit:
            console_output = captured_output.getvalue()
            self.assertRegex(console_output, "CorruptedJavacoreException")
        finally:
            sys.stdout = default_output  # Reset redirect.

    def test_error_javacore_files_corrupted(self):
        # Run with params from https://stackoverflow.com/questions/18668947/how-do-i-set-sys-argv-so-i-can-unit-test-it
        # Redirect console from https://stackoverflow.com/questions/33767627/python-write-unittest-for-console-print
        default_output = sys.stdout
        captured_output = io.StringIO()  # Create StringIO object
        sys.stdout = captured_output  # and redirect stdout.
        try:
            with patch.object(sys, 'argv', self.javacorefilescorrupted):
                javacore_analyser_batch.main()
        except SystemExit:
            console_output = captured_output.getvalue()
            self.assertRegex(console_output, "Error during processing file:")
        finally:
            sys.stdout = default_output  # Reset redirect.

    def runMainWithParams(self, args):
        # From https://stackoverflow.com/questions/18668947/how-do-i-set-sys-argv-so-i-can-unit-test-it
        with patch.object(sys, 'argv', args):
            javacore_analyser_batch.main()
        self.assert_data_generated_and_not_empty()

    # Checks whether report.xml and report.xsl have been generated.
    def assert_data_generated_and_not_empty(self):
        self.assertTrue(os.path.exists("tmp/index.html"), "index.html not generated")
        self.assertTrue(os.path.getsize("tmp/index.html") > 0, "index.html file is empty")
        self.assertTrue(os.path.exists("tmp/threads"))
        self.assertGreaterEqual(self.number_files_in_dir("tmp/threads"), 1)
        self.assertTrue(os.path.exists("tmp/javacores"))
        self.assertGreaterEqual(self.number_files_in_dir("tmp/javacores"), 1)
        self.assertTrue(os.path.isfile("tmp/wait2-debug.log"))

    @staticmethod
    def number_files_in_dir(path):
        return len(os.listdir(path))

    def tearDown(self):
        # From https://stackoverflow.com/questions/12034393/import-side-effects-on-logging
        root = logging.getLogger()
        for handler in root.handlers.copy():
            root.removeHandler(handler)
            handler.close()

        rm_tmp_dir()
