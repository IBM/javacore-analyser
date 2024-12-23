#
# Copyright IBM Corp. 2024 - 2024
# SPDX-License-Identifier: Apache-2.0
#
import argparse

from javacore_analyser import javacore_analyser_batch, constants


def main():
    parser = argparse.ArgumentParser()

    type_arg = parser.add_argument("type", choices=["batch", "web"], default="batch",
                                   help="Application type")

    batch_group = parser.add_argument_group("batch", description="Run batch application")
    batch_group.add_argument("input", help="Input file(s) or directory")
    batch_group.add_argument("output", help="Destination report directory")
    batch_group.add_argument("--separator", default=constants.DEFAULT_FILE_DELIMITER)

    web_group = parser.add_argument_group("web", description="Run web application")
    web_group.add_argument("--port", help="Application port", default=constants.DEFAULT_PORT)
    web_group.add_argument("--reports_directory", help="Directory to store reports data",
                           default=constants.DEFAULT_REPORTS_DIR)

    args = parser.parse_args()

    app_type: str = args.type

    if app_type.lower() == "web":
        print("Running web application")
    elif app_type.lower() == "batch":
        print("Running batch application")
        javacore_analyser_batch.batch_process(args.input, args.output, args.separator)
    else:
        print('Invalid application type. Available types: "batch" or "web"')


if __name__ == '__main__':
    main()
