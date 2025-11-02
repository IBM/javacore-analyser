#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

from src.javacore_analyser.ai.prompter import Prompter


class AiOverviewPrompter(Prompter):

    def construct_prompt(self):
        prompt = 'Given the information below, explain how to improve the performance of the java application\n'
        prompt += 'Java configuration:\n'
        prompt += 'Number of CPUs: ' + self.javacore_set.number_of_cpus + '\n'
        prompt += 'Xmx=' + self.javacore_set.xmx + '\n'
        prompt += 'Xms=' + self.javacore_set.xms + '\n'
        prompt += 'Xmn=' + self.javacore_set.xmn + '\n'
        prompt += 'GC policy: ' + self.javacore_set.gc_policy + '\n'
        prompt += 'Compressed references: ' + str(self.javacore_set.compressed_refs) + '\n'
        prompt += 'Verbose GC: ' + str(self.javacore_set.verbose_gc) + '\n'
        prompt += 'OS level: ' + self.javacore_set.os_level + '\n'
        prompt += 'System architecture: ' + self.javacore_set.architecture + '\n'
        prompt += 'Java version: ' + self.javacore_set.java_version + '\n'
        # jvm_start_time = ""
        prompt += 'Command line: ' + self.javacore_set.cmd_line + '\n'
        # prompt += self.javacore_set.user_args = []
        return prompt
