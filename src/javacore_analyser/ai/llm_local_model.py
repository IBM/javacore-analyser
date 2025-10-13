#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import ollama


class LLMLocalModel:

    def __init__(self):
        self.model = 'ibm/granite4:micro'
        ollama.pull(self.model)

    def generate_response(self, text):
        return ollama.generate(model=self.model, prompt=text).response  
