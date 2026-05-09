#
# Copyright IBM Corp. 2026
# SPDX-License-Identifier: Apache-2.0
#

import os
from pathlib import Path

class Prompter:

    def __init__(self, javacore_set):
        self.javacore_set = javacore_set

    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load a prompt template from the data/prompts directory.
        
        Args:
            template_name: Name of the template file (e.g., 'performance_recommendations_prompt.txt')
            
        Returns:
            str: Content of the template file
            
        Raises:
            FileNotFoundError: If the template file doesn't exist
        """
        # Get the directory where this module is located
        current_dir = Path(__file__).parent.parent
        template_path = current_dir / 'data' / 'prompts' / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def construct_prompt(self) -> str:
        return ""