#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import locale
import logging
import os
import re
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from waitress import serve

import javacore_analyser.javacore_analyser_batch
from javacore_analyser import common_utils
from javacore_analyser.common_utils import create_console_logging, create_file_logging
from javacore_analyser.constants import TEMP_DIR
from javacore_analyser.properties import Properties

"""
To run the application from cmd type:

flask --app javacore_analyser_web run
"""
app = Flask(__name__, static_folder='data')
reports_dir = 'reports' # This is default value. It will be changed in the constructor


# Assisted by watsonx Code Assistant
def create_temp_data_in_reports_dir(directory):
    tmp_reports_dir = os.path.join(directory, TEMP_DIR)
    if os.path.isdir(tmp_reports_dir):
        shutil.rmtree(tmp_reports_dir, ignore_errors=True)
    os.mkdir(tmp_reports_dir)


@app.route('/')
def index():
    reports = [{"name": Path(f).name, "date": time.ctime(os.path.getctime(f)), "timestamp": os.path.getctime(f)}
               for f in os.scandir(reports_dir) if f.is_dir() and Path(f).name is not TEMP_DIR]
    reports.sort(key=lambda item: item["timestamp"], reverse=True)
    return render_template('index.html', reports=reports)


@app.route('/reports/<path:path>')
def dir_listing(path):
    return send_from_directory(reports_dir, path)


@app.route('/zip/<path:path>')
# Assisted by watsonx Code Assistant 
def compress(path):
    """
    Compress a directory and return the compressed file as an attachment.

    Args:
        path (str): The path to the directory to compress.

    Returns:
        send_from_directory: The compressed file as an attachment.
    """
    temp_zip_dir = tempfile.TemporaryDirectory()
    try:
        temp_zip_dir_name = temp_zip_dir.name
        zip_filename = path + ".zip"
        report_location = os.path.join(reports_dir, path)
        shutil.make_archive(os.path.join(temp_zip_dir_name, path), 'zip', report_location)
        logging.debug("Generated zip file location:" + os.path.join(temp_zip_dir_name, zip_filename))
        logging.debug("Temp zip dir name: " + temp_zip_dir_name)
        logging.debug("Zip filename: " + zip_filename)
        return send_from_directory(temp_zip_dir_name, zip_filename, as_attachment=True)
    finally:
        temp_zip_dir.cleanup()


@app.route('/delete/<path:path>')
def delete(path):
    # Checking if the report exists. This is to prevent attempt to delete any data by deleting any file outside
    # report dir if you prepare path variable.
    # Prevent deletion of TEMP_DIR and nested paths
    if path == TEMP_DIR or '/' in path or '\\' in path:
        logging.error(f"Invalid report path: {path}. Cannot delete system directories or nested paths.")
        return "Cannot delete this directory.", 403

    report_location = os.path.normpath(os.path.join(reports_dir, path))
    if not report_location.startswith(reports_dir):
        logging.error(f"Path traversal attempt detected: {path}")
        return "Cannot delete the report.", 403

    # Additional check: ensure it's a direct child
    if os.path.dirname(report_location) != reports_dir:
        logging.error(f"Attempt to delete non-direct child: {path}")
        return "Cannot delete the report.", 403

    shutil.rmtree(report_location)

    return redirect("/")


# Assisted by WCA@IBM
# Latest GenAI contribution: ibm/granite-20b-code-instruct-v2
@app.route('/upload', methods=['POST'])
def upload_file():

    report_name = request.values.get("report_name")
    report_name = re.sub(r'[^a-zA-Z0-9]', '_', report_name)

    # Create a temporary directory to store uploaded files
    # Note We have to use permanent files and then delete them.
    # tempfile.Temporary_directory function does not work when you want to access files from another threads.
    javacores_temp_dir_name = os.path.normpath(os.path.join(reports_dir, TEMP_DIR, report_name))
    if not javacores_temp_dir_name.startswith(reports_dir):
        raise Exception("Security exception: Uncontrolled data used in path expression")

    try:
        os.mkdir(javacores_temp_dir_name)

        # Get the list of files from webpage
        files = request.files.getlist("files")

        input_files = []
        # Iterate for each file in the files List, and Save them
        for file in files:
            # Sanitize filename to prevent path traversal
            safe_filename = os.path.basename(file.filename) if file.filename else None
            if not safe_filename:
                continue  # Skip files with invalid names
            file_name = os.path.join(javacores_temp_dir_name, safe_filename)
            file.save(file_name)
            input_files.append(file_name)

        # Process the uploaded file
        report_output_dir = os.path.join(reports_dir, report_name)
        processing_thread = threading.Thread(
            target=javacore_analyser.javacore_analyser_batch.process_javacores_and_generate_report_data,
            name="Processing javacore data", args=(input_files, report_output_dir)
        )
        processing_thread.start()

        time.sleep(1)  # Give 1 second to generate index.html in processing_thread before redirecting
        # Use url_for() to generate a safe redirect URL to prevent open redirect vulnerability
        return redirect(url_for('dir_listing', path=f"{report_name}/index.html"))
    finally:
        shutil.rmtree(javacores_temp_dir_name, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    common_utils.add_web_args(parser)
    common_utils.add_common_args(parser)
    args = parser.parse_args()
    Properties.get_instance().load_properties(args)
    debug = Properties.get_instance().get_property("debug", False)
    port = Properties.get_instance().get_property("port", 5000)
    reports_directory = Properties.get_instance().get_property("reports_dir")
    ai = Properties.get_instance().get_property("use_ai", False)

    run_web(debug, port, reports_directory, ai)


def run_web(debug=False, port=5000, reports_directory="reports", ai=False):
    global reports_dir
    reports_dir = os.path.abspath(reports_directory)
    create_console_logging()
    logging.info("Javacore analyser")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())
    logging.info("Reports directory: " + reports_dir)
    logging.info("AI: " + str(ai))
    create_file_logging(reports_dir)
    create_temp_data_in_reports_dir(reports_dir)
    if debug:
        app.run(debug=True, port=port)  # Run Flask for development
    else:
        serve(app, port=port)  # Run Waitress in production


if __name__ == '__main__':
    """
    The application passes the following environmental variables:
    DEBUG (default: False) - defines if we should run an app in debug mode
    PORT - application port
    REPORTS_DIR - the directory when the reports are stored as default
    """
    main()
