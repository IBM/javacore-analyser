#
# Copyright IBM Corp. 2024 - 2026
# SPDX-License-Identifier: Apache-2.0
#
# This module is kept for backward compatibility.
# The implementation has moved to javacore_analyzer.py.
# New code should import JavacoreAnalyzer from javacore_analyser.javacore_analyzer.
#

import warnings

from javacore_analyser.javacore_analyzer import JavacoreAnalyzer

# Re-export FileResolver and the module-level helper so any code that imported
# them directly from javacore_set keeps working.
from javacore_analyser.file_resolver import FileResolver


class JavacoreSet(JavacoreAnalyzer):
    """Backward-compatible alias for JavacoreAnalyzer. This is currently used in tests only.

    .. deprecated::
        Use :class:`~javacore_analyser.javacore_analyzer.JavacoreAnalyzer` instead.
        This class will be removed in a future release.
    """

    def __init__(self, path):
        warnings.warn(
            "JavacoreSet is deprecated. Use JavacoreAnalyzer from "
            "javacore_analyser.javacore_analyzer instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(path)
