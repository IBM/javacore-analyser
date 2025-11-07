#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import logging
import markdown
from ollama import chat
from ollama import ChatResponse
import ollama

from javacore_analyser.constants import DEFAULT_LLM_MODEL



# prerequisites:
# install Ollama from https://ollama.com/download

class Ai:
    """
    A class representing an AI model infuser.

    Attributes:
        prompt (str): The current prompt being infused.
        javacore_set (set): A set of Java cores for the AI model.
        model (str): The AI model to be used for inference.
    """

    def __init__(self, javacore_set):
        self.prompt = ""
        self.javacore_set = javacore_set
        self.model = DEFAULT_LLM_MODEL
        logging.info("Pulling model: " + self.model)
        ollama.pull(self.model)
        logging.info("Model pulled: " + self.model)


    def set_model(self, model):
        self.model = model


    def infuse(self, prompter):
        content = ""
        self.prompt = prompter.construct_prompt()
        if self.prompt and len(self.prompt) > 0:
            logging.debug("Infusing prompt: " + self.prompt[40] + "...")
            response: ChatResponse = chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': self.prompt,
                },
            ])
            logging.debug("Infused finished")
            content = response.message.content
        return content
    
    def response_to_html(self, response):
        html = markdown.markdown(response)
        return html
    
    def infuse_in_html(self, prompter):
        content = self.infuse(prompter)
        return self.response_to_html(content)
        