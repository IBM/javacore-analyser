#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

from javacore_analyser.ai.prompter import Prompter


class TipsPrompter(Prompter) :

    def construct_prompt(self):
        prompt = ""
        if len(self.javacore_set.tips) > 0:
            prompt = "Analyse the tips to help identify performance bottlenecks in a Java application: \n"
            for tip in self.javacore_set.tips:
                for message in tip:
                    prompt += message + '\n'
        return prompt