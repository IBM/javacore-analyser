#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import logging

import markdown
import ollama
from ollama import ChatResponse
from ollama import chat

from javacore_analyser.ai.llm import LLM
from javacore_analyser.properties import Properties


# prerequisites:
# install Ollama from https://ollama.com/download

class OllamaLLM(LLM):
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
        self.model = Properties.get_instance().get_property("llm_model", "ibm/granite4:latest")
        self.temperature = Properties.get_instance().get_property("llm_temperature", 0.8)
        self.max_tokens = Properties.get_instance().get_property("llm_max_tokens", 1000)
        logging.info("Pulling model: " + self.model)
        ollama.pull(self.model)
        logging.info("Model pulled: " + self.model)


    def set_model(self, model):
        self.model = model


    def infuse(self, prompter):
        content = ""
        self.prompt = prompter.construct_prompt()
        if self.prompt and len(self.prompt) > 0:
            logging.debug("Infusing prompt: " + self.prompt)
            response: ChatResponse = chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': self.prompt,
                },
            ], options={'temperature': self.temperature, 'num_ctx': self.max_tokens})
            logging.debug("Infused finished")
            content = response.message.content
        return content
    
    def response_to_html(self, response):
        html = markdown.markdown(response)
        return html


    def infuse_in_html(self, prompter):
        content = self.infuse(prompter)
        return self.response_to_html(content)
        