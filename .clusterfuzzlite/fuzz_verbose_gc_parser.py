#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# Fuzz target for VerboseGcFile XML parsing.
# Exercises the verbose GC log parser with arbitrary XML-like byte sequences
# by writing them to a temporary file and parsing via VerboseGcFile.
#
import os
import sys
import tempfile
import atheris

with atheris.instrument_imports():
    from javacore_analyser.verbose_gc import VerboseGcFile, GcVerboseProcessingException


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    content = fdp.ConsumeUnicodeNoSurrogates(4096)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name
    try:
        VerboseGcFile(tmp_path)
    except GcVerboseProcessingException:
        # Expected for malformed XML; these are not bugs.
        pass
    except Exception:
        raise
    finally:
        os.unlink(tmp_path)


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
