#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#

import logging

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from javacore_analyser.ai.llm import LLM
from javacore_analyser.properties import Properties


class WatsonxLLM(LLM):
    """
    A class representing a WatsonX AI model integration.

    This class provides integration with IBM WatsonX.ai for remote LLM inference,
    allowing the javacore analyser to leverage cloud-based AI models.

    Attributes:
        javacore_set (set): A set of Java cores for the AI model.
        model (str): The AI model identifier to be used for inference.
        api_client (APIClient): WatsonX API client for authentication.
        model_inference (ModelInference): WatsonX model inference instance.
    """

    def __init__(self, javacore_set):
        super().__init__(javacore_set)
        
        # Get WatsonX configuration from properties
        self.model = Properties.get_instance().get_property("llm", "ibm/granite-13b-chat-v2")
        api_key = Properties.get_instance().get_property("watsonx_api_key", None)
        project_id = Properties.get_instance().get_property("watsonx_project_id", None)
        url = Properties.get_instance().get_property("watsonx_url", "https://us-south.ml.cloud.ibm.com")
        
        if not api_key:
            raise ValueError("watsonx_api_key must be configured in properties")
        if not project_id:
            raise ValueError("watsonx_project_id must be configured in properties")
        
        logging.info(f"Initializing WatsonX LLM with model: {self.model}")
        
        # Initialize WatsonX credentials and API client
        credentials = Credentials(
            url=url,
            api_key=api_key
        )
        
        self.api_client = APIClient(credentials)
        
        # Initialize model inference
        self.model_inference = ModelInference(
            model_id=self.model,
            api_client=self.api_client,
            project_id=project_id
        )
        
        # Build WatsonX-specific generation parameters
        self.params = self._build_watsonx_params()
        
        logging.info("WatsonX LLM initialized successfully")

    def _build_watsonx_params(self):
        """
        Build WatsonX-specific generation parameters.
        
        :return: Dictionary with WatsonX generation parameters
        :rtype: dict
        """
        params = {}
        
        if self.temperature is not None:
            params[GenParams.TEMPERATURE] = float(self.temperature)
        
        if self.max_tokens is not None:
            params[GenParams.MAX_NEW_TOKENS] = int(self.max_tokens)
        
        # Add default parameters if not specified
        if GenParams.DECODING_METHOD not in params:
            params[GenParams.DECODING_METHOD] = "greedy"
        
        logging.info(f"Built WatsonX generation params: {params}")
        return params

    def infuse(self, prompter):
        """
        Process the input prompter using WatsonX AI model.

        This method constructs a prompt from the prompter, sends it to WatsonX,
        and returns the generated response.

        :param prompter: The prompter object containing the prompt construction logic.
        :type prompter: Prompter
        :return: The generated response from WatsonX.
        :rtype: str
        """
        content = ""
        self.prompt = prompter.construct_prompt()
        
        if self.prompt and len(self.prompt) > 0:
            logging.debug("Infusing prompt with WatsonX")
            
            try:
                # Generate response using WatsonX
                response = self.model_inference.generate_text(
                    prompt=self.prompt,
                    params=self.params if self.params else None
                )
                
                logging.debug("WatsonX infusion finished")
                content = response
                
            except Exception as e:
                logging.error(f"Error during WatsonX inference: {str(e)}")
                raise
        
        return content

# Made with Bob
