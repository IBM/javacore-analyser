#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import locale
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory, redirect
from waitress import serve

import javacore_analyser.javacore_analyser_batch
from javacore_analyser.constants import DEFAULT_REPORTS_DIR, DEFAULT_PORT
from javacore_analyser.logging_utils import create_console_logging, create_file_logging

"""
To run the application from cmd type:
export REPORTS_DIR=/tmp/reports
flask --app javacore_analyser_web run
"""
app = Flask(__name__)
with app.app_context():
    create_console_logging()
    logging.info("Javacore analyser")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())
    reports_dir = os.getenv("REPORTS_DIR", DEFAULT_REPORTS_DIR)
    logging.info("Reports directory: " + reports_dir)
    create_file_logging(reports_dir)


@app.route('/')
def index():
    reports = [{"name": Path(f).name, "date": time.ctime(os.path.getctime(f)), "timestamp": os.path.getctime(f)}
               for f in os.scandir(reports_dir) if f.is_dir()]
    reports.sort(key=lambda item: item["timestamp"], reverse=True)
    return render_template('index.html', reports=reports)


@app.route('/reports/<path:path>')
def dir_listing(path):
    return send_from_directory(reports_dir, path)


@app.route('/zip/<path:path>')
def compress(path):
    try:
        temp_zip_dir = tempfile.TemporaryDirectory()
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
    reports_list = os.listdir(reports_dir)
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
    try:
        # Create a temporary directory to store uploaded files
        javacores_temp_dir = tempfile.TemporaryDirectory()
        javacores_temp_dir_name = javacores_temp_dir.name

        # Get the list of files from webpage
        files = request.files.getlist("files")

        input_files = []
        # Iterate for each file in the files List, and Save them
        for file in files:
            file_name = os.path.join(javacores_temp_dir_name, file.filename)
            file.save(file_name)
            input_files.append(file_name)

        report_name = request.values.get("report_name")
        report_name = re.sub(r'[^a-zA-Z0-9]', '_', report_name)

        # Process the uploaded file
        report_output_dir = reports_dir + '/' + report_name
        javacore_analyser.javacore_analyser_batch.process_javacores_and_generate_report_data(input_files,
                                                                                             report_output_dir)

        return redirect("/reports/" + report_name + "/index.html")
    finally:
        javacores_temp_dir.cleanup()

def main():
    debug = os.getenv("DEBUG", False)
    port = os.getenv("PORT", DEFAULT_PORT)
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
