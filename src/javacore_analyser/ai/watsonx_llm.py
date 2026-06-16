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
        """
        Initialize WatsonX LLM with authentication and model configuration.
        
        This method sets up the WatsonX AI client using IBM Cloud credentials and
        initializes the model inference instance for generating AI responses.
        
        :param javacore_set: A set of Java cores to be analyzed by the AI model.
        :type javacore_set: JavacoreSet
        :raises ValueError: If watsonx_api_key or watsonx_project_id is not configured.
        :raises InvalidCredentialsError: If the API key is invalid, expired, or is a JWT token.
        
        .. note::
            **API Key Requirements:**
            
            - Must be a permanent IBM Cloud API key (not a JWT access token)
            - JWT tokens which expire after 1 hour - these will NOT work
            - Get your API key from: https://cloud.ibm.com/iam/apikeys
            
            **Common Authentication Errors:**
            
            - "Provided API key could not be found" - You're using a JWT token instead of an API key
            - "API key expired" - Generate a new API key from IBM Cloud console
            - "Invalid credentials" - Verify your API key is correct and has proper permissions

        """
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
        self.project_id = project_id
        
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
            logging.info(f"Infusing prompt with WatsonX (prompt length: {len(self.prompt)} chars)")
            logging.debug(f"Full prompt:\n{self.prompt[:1000]}...")  # Log first 1000 chars
            
            try:
                # Use chat API for better results with modern models
                # Format prompt as a chat message
                messages = [
                    {
                        "role": "user",
                        "content": self.prompt
                    }
                ]
                
                logging.debug("Using WatsonX chat API for inference")
                
                # Generate response using WatsonX chat API
                response = self.model_inference.chat(
                    messages=messages,
                    params=self.params if self.params else None
                )
                
                logging.info("WatsonX infusion finished")
                
                # Extract content from chat response
                if isinstance(response, dict) and 'choices' in response:
                    content = response['choices'][0]['message']['content']
                elif isinstance(response, str):
                    content = response
                else:
                    content = str(response)
                
                logging.info(f"Generated response length: {len(content)} chars")
                logging.debug(f"Full response:\n{content}")
                
                # Check if response seems incomplete
                if len(content) < 100:
                    logging.warning(f"Response seems unusually short ({len(content)} chars). This may indicate truncation or an issue with the model.")
                
            except AttributeError:
                # Fallback to generate_text if chat is not available
                logging.warning("Chat API not available, falling back to generate_text")
                try:
                    response = self.model_inference.generate_text(
                        prompt=self.prompt,
                        params=self.params if self.params else None
                    )
                    content = response
                    logging.info(f"Generated response length: {len(content)} chars")
                except Exception as e:
                    logging.error(f"Error during WatsonX text generation: {str(e)}")
                    raise
            except Exception as e:
                logging.error(f"Error during WatsonX inference: {str(e)}")
                raise
        else:
            logging.warning("Empty prompt provided to WatsonX LLM")
        
        return content

# Made with Bob
