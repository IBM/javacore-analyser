#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import sys

from javacore_analyser import javacore_analyser_batch, common_utils
from javacore_analyser.properties import Properties


def main():
    parser = argparse.ArgumentParser(prog="python -m javacore_analyser")

    subparsers = parser.add_subparsers(dest="type", help="Application type", required=True)

    batch = subparsers.add_parser("batch", description="Run batch application")
    batch.add_argument("input", help="Input file(s) or directory")
    batch.add_argument("output", help="Destination report directory")
    common_utils.add_common_args(parser)

    web = subparsers.add_parser("web", description="Run web application")
    common_utils.add_web_args(web)

    args = parser.parse_args()

    Properties.get_instance().load_properties(args)

    app_type: str = args.type

    if app_type.lower() == "web":
        print("Running web application")
        try:
            from javacore_analyser import javacore_analyser_web
            javacore_analyser_web.run_web(args.debug, args.port, args.reports_dir, ai=Properties.get_instance().get_property("use_ai"))
        except ImportError as e:
            print(f"Error: Web mode requires Flask. Install with: pip install javacore_analyser[web]")
            print(f"Details: {e}")
            sys.exit(1)
    elif app_type.lower() == "batch":
        print("Running batch application")
        javacore_analyser_batch.batch_process(args.input, args.output)
    else:
        print('Invalid application type. Available types: "batch" or "web"')


if __name__ == '__main__':
    # This is the code to be able to run the app from command line.
    # Try this:
    # python -m javacore_analyser -h
    main()
