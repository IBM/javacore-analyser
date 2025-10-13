#
# Copyright IBM Corp. 2025 - 2025
# SPDX-License-Identifier: Apache-2.0
#

import logging
from transformers import AutoModelForCausalLM, AutoTokenizer


class LLMLocalModel:

    def __init__(self):
        logging.info("Initialising LLM Local Model")
        self.device = "cpu"
        self.max_tokens = 50
        self.model_path = "ibm-granite/granite-4.0-h-micro"
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
        self.model.eval()
        logging.info("LLM Local Model Initialised")


    def generate_response(self, text):
        chat = [{ "role": "user", "content": text },]
        tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        chat = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        input_tokens = tokenizer(chat, return_tensors="pt").to(self.device)
        output = self.model.generate(**input_tokens, max_new_tokens=self.max_tokens)
        output = tokenizer.batch_decode(output)
        return output[0]