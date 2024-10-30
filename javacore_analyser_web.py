#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import locale
import logging
import shutil

import logging_utils
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory, redirect, send_file

import javacore_analyzer
from constants import DEFAULT_REPORTS_DIR, DEFAULT_PORT

app = Flask(__name__)
with app.app_context():
    logging_utils.create_console_logging()
    logging.info("Javacore analyser")
    logging.info("Python version: " + sys.version)
    logging.info("Preferred encoding: " + locale.getpreferredencoding())
    reports_dir = os.getenv("REPORTS_DIR", DEFAULT_REPORTS_DIR)
    logging.info("Reports directory: " + reports_dir)
    logging_utils.create_file_logging(reports_dir)


@app.route('/')
def index():
    reports = [Path(f).name for f in os.scandir(reports_dir) if f.is_dir()]
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
        logging.debug("Generated zip file location:" + os.path.join(temp_zip_dir_name,zip_filename))
        logging.debug("Temp zip dir name: " + temp_zip_dir_name)
        logging.debug("Zip filename: " + zip_filename)
        return send_from_directory(temp_zip_dir_name, zip_filename, as_attachment=True)
    finally:
        temp_zip_dir.cleanup()

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

        if len(input_files) == 1:
            report_name = Path(input_files[0]).name
        else:
            report_name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_name = re.sub(r'[^a-zA-Z0-9]', '_', report_name)

        # Process the uploaded file
        report_output_dir = reports_dir + '/' + report_name
        javacore_analyzer.process_javacores_and_generate_report_data(input_files, report_output_dir)

        return redirect("/reports/" + report_name + "/index.html")
    finally:
        javacores_temp_dir.cleanup()


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", DEFAULT_PORT))
