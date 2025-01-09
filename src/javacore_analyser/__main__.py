#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import argparse

from javacore_analyser import javacore_analyser_batch, constants, javacore_analyser_web


def main():
    parser = argparse.ArgumentParser(prog="python -m javacore_analyser")
    subparsers = parser.add_subparsers(dest="type", help="Application type", required=True)

    batch = subparsers.add_parser("batch", description="Run batch application")
    batch.add_argument("input", help="Input file(s) or directory")
    batch.add_argument("output", help="Destination report directory")
    batch.add_argument("--separator", default=constants.DEFAULT_FILE_DELIMITER)

    web = subparsers.add_parser("web", description="Run web application")
    web.add_argument("--debug", help="Debug mode. Use True only for app development", default=False)
    web.add_argument("--port", help="Application port", default=constants.DEFAULT_PORT)
    web.add_argument("--reports-dir", help="Directory to store reports data",
                     default=constants.DEFAULT_REPORTS_DIR)

    args = parser.parse_args()

    app_type: str = args.type

    if app_type.lower() == "web":
        print("Running web application")
        javacore_analyser_web.run_web(args.debug, args.port, args.reports_dir)
    elif app_type.lower() == "batch":
        print("Running batch application")
        javacore_analyser_batch.batch_process(args.input, args.output, args.separator)
    else:
        print('Invalid application type. Available types: "batch" or "web"')


if __name__ == '__main__':
    # This is the code to be able to run the app from command line.
    # Try this:
    # python -m javacore_analyser -h
    main()
