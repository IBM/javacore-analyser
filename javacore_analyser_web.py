#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import os
import tempfile

# Assisted by WCA@IBM
# Latest GenAI contribution: ibm/granite-20b-code-instruct-v2
from flask import Flask, render_template, request

import javacore_analyzer

REPORTS_DIR = "reports"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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

    # Process the uploaded file
    javacore_analyzer.process_javacores_and_generate_report_data(input_files, REPORTS_DIR)

if __name__ == '__main__':
    app.run(debug=True)
