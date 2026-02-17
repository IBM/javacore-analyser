#
# Copyright IBM Corp. 2026 - 2026
# SPDX-License-Identifier: Apache-2.0
#


class InvalidLLMMethodError(ValueError):
    """
    Exception raised when an invalid LLM method is specified.
    
    This exception is raised when the LLM method provided is not one of the
    supported methods (e.g., 'ollama' or 'huggingface').
    """
    
    def __init__(self, llm_method: str, supported_methods: list = None):
        """
        Initialize the InvalidLLMMethodError.
        
        Args:
            llm_method: The invalid LLM method that was provided
            supported_methods: Optional list of supported LLM methods
        """
        self.llm_method = llm_method
        self.supported_methods = supported_methods or ['ollama', 'huggingface']
        
        message = f"Invalid LLM method: '{llm_method}'. Supported methods are: {', '.join(self.supported_methods)}"
        super().__init__(message)

# Made with Bob
