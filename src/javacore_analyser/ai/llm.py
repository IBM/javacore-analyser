# Assisted by watsonx Code Assistant

from abc import ABC, abstractmethod

import markdown

from javacore_analyser.properties import Properties


class LLM(ABC):
    """
    Abstract Base Class for Language Learning Model (LLM).
    """

    def __init__(self, javacore_set):
        self.javacore_set = javacore_set
        self.temperature = Properties.get_instance().get_property("llm_temperature", 0.8)
        self.max_tokens = Properties.get_instance().get_property("llm_max_tokens", 1000)

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

        :param response: The text to be converted to HTML.
        :type response: str
        :return: The HTML formatted string.
        :rtype: str
        """
        html = markdown.markdown(response)
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
