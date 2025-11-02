#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

from ollama import chat
from ollama import ChatResponse

from src.javacore_analyser.constants import DEFAULT_MODEL


# prerequisites:
# install Ollama from https://ollama.com/download
# > ollama pull granite3.3:8b
# > ollama pull granite-code:3b
# > pip install ollama

class Ai:

    def __init__(self, javacore_set):
        self.prompt = ""
        self.javacore_set = javacore_set
        self.model = DEFAULT_MODEL


    def set_model(self, model):
        self.model = model


    def infuse(self, prompter):
        content = ""
        self.prompt = prompter.construct_prompt()
        if self.prompt and len(self.prompt) > 0:
            response: ChatResponse = chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': self.prompt,
                },
            ])
            content = response.message.content
            content = content.replace('\n', '<br/>')
        return content