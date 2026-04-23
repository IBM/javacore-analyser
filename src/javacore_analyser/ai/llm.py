#
# Copyright IBM Corp. 2025 - 2026
# SPDX-License-Identifier: Apache-2.0
#

from abc import ABC, abstractmethod
import logging

import markdown

from javacore_analyser.properties import Properties


class LLM(ABC):
    """
    Abstract Base Class for Language Learning Model (LLM).
    """

    def __init__(self, javacore_set):
        self.javacore_set = javacore_set
        temp_value = Properties.get_instance().get_property("llm_temperature", "default")
        max_tokens_value = Properties.get_instance().get_property("llm_max_tokens", "default")
        
        # Set to None if "default" is specified, otherwise use the value
        self.temperature = None if str(temp_value).lower() == "default" else temp_value
        self.max_tokens = None if str(max_tokens_value).lower() == "default" else max_tokens_value
        
        # Build default params dict with standard parameter names
        self.params = self._build_generation_params(
            temperature='temperature',
            max_tokens='max_tokens'
        )

    def _build_generation_params(self, **param_mapping):
        """
        Build a dictionary of generation parameters, excluding None values.
        
        :param param_mapping: Keyword arguments mapping parameter names to their values.
                             For example: temperature='temperature', max_tokens='max_new_tokens'
        :return: Dictionary with only non-None parameters
        :rtype: dict
        """
        params = {}
        for param_name, config_attr in param_mapping.items():
            value = getattr(self, config_attr, None)
            if value is not None:
                params[param_name] = value
        logging.info(f"Built generation params: {params}")
        return params

    @abstractmethod
    def infuse(self, prompter):
        """
        Abstract method to process the input prompter.

        This method should be implemented by concrete subclasses.
        It takes a prompter (a string) as input and returns a processed response.

        :param prompter: The input string to be processed.
        :type prompter: str
        """
        pass

    def response_to_html(self, response):
        """
        Convert the given response text into HTML format.

        This method uses the markdown library to convert plain text to HTML.
        Line breaks in the input text are preserved as <br> tags in the output.

        :param response: The text to be converted to HTML.
        :type response: str
        :return: The HTML formatted string.
        :rtype: str
        """
        html = markdown.markdown(response, extensions=['nl2br'])
        logging.info(f"Converted response to HTML: {html}")
        return html

    def infuse_in_html(self, prompter):
        """
        Process the input prompter and return the result in HTML format.

        This method first calls the infuse method to process the prompter,
        then converts the resulting text into HTML using the response_to_html method.

        :param prompter: The input string to be processed.
        :type prompter: str
        :return: The HTML formatted string.
        :rtype: str
        """
        content = self.infuse(prompter)
        return self.response_to_html(content)
