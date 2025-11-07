#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.ai.prompter import Prompter


# Assisted by watsonx Code Assistant

class AiOverviewPrompter(Prompter):
    """
    AiOverviewPrompter class generates a detailed prompt for explaining overview section.

    Attributes:
        - javacore_set (JavacoreSet): An object containing Java configuration details.
    """

    def construct_prompt(self):
        prompt = f'''
        Given the information below, explain how to improve the performance of the java application
        Java configuration:
        Number of CPUs: {self.javacore_set.number_of_cpus}
        Xmx={self.javacore_set.xmx}
        Xms={self.javacore_set.xms}
        Xmn={self.javacore_set.xmn}
        GC policy: {self.javacore_set.gc_policy}
        Compressed references: {self.javacore_set.compressed_refs}
        Verbose GC: {self.javacore_set.verbose_gc}
        OS level: {self.javacore_set.os_level}
        System architecture: {self.javacore_set.architecture}
        Java version: {self.javacore_set.java_version}
        Command line: {self.javacore_set.cmd_line}
        '''
        return prompt
