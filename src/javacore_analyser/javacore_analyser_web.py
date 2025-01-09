#
# Copyright IBM Corp. 2024 - 2024
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

from flask import Flask, render_template, request, send_from_directory, redirect
from waitress import serve

import javacore_analyser.javacore_analyser_batch
from javacore_analyser.constants import DEFAULT_REPORTS_DIR, DEFAULT_PORT, TEMP_DIR
from javacore_analyser.logging_utils import create_console_logging, create_file_logging

"""
To run the application from cmd type:

flask --app javacore_analyser_web run
"""
app = Flask(__name__)
reports_dir = DEFAULT_REPORTS_DIR


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
def compress(path):
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
    # reports_list = os.listdir(reports_dir)
    report_location = os.path.normpath(os.path.join(reports_dir, path))
    if not report_location.startswith(reports_dir):
        logging.error("Deleted report in report list. Not deleting")
        return "Cannot delete the report.", 503
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
            file_name = os.path.join(javacores_temp_dir_name, file.filename)
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
        return redirect("/reports/" + report_name + "/index.html")
    finally:
        shutil.rmtree(javacores_temp_dir_name, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="Debug mode. Use only for development", default=False)
    parser.add_argument("--port", help="Port to run application", default=DEFAULT_PORT)
    parser.add_argument("--reports-dir", help="Directory where app reports are stored",
                        default=DEFAULT_REPORTS_DIR)
    args = parser.parse_args()
    debug = args.debug
    port = args.port
    reports_directory = args.reports_dir

    run_web(debug, port, reports_directory)


def run_web(debug=False, port=5000, reports_directory=DEFAULT_REPORTS_DIR):
    global reports_dir
    reports_dir = reports_directory
    create_console_logging()
    logging.info("Javacore analyser")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())
    logging.info("Reports directory: " + reports_dir)
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
