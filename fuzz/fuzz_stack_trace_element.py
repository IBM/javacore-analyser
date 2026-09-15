#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# Fuzz target for StackTraceElement.set_line()
# Exercises the line-parsing logic that handles arbitrary javacore text input.
#
import sys
import atheris

with atheris.instrument_imports():
    from javacore_analyser.stack_trace_element import StackTraceElement


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    line = fdp.ConsumeUnicodeNoSurrogates(256)
    try:
        element = StackTraceElement(line)
    except Exception:
        # Unexpected exceptions from arbitrary text input are the bug we are looking for;
        # all other exceptions (ValueError, etc.) from malformed data are acceptable.
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
