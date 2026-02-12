import logging

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from javacore_analyser.ai.llm import LLM
from javacore_analyser.constants import ASSISTANT_ROLE, END_OF_TEXT
from javacore_analyser.properties import Properties


# Assisted by watsonx Code Assistant

class HuggingFaceLLM(LLM):
    """
    HuggingFaceLLM class for loading and utilizing HuggingFace's language models.

    Attributes:
        javacore_set (set): Set of Java cores.
        device (str): Device type ('cpu' or accelerator type).
        model (AutoModelForCausalLM): HuggingFace's pre-trained model for causal language modeling.
        tokenizer (AutoTokenizer): HuggingFace's tokenizer for the model.
    """

    def __init__(self, javacore_set):
        super().__init__(javacore_set)
        logging.info("Loading HuggingFaceFace_LLM")
        # self.device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
        self.device = "cpu"
        logging.info(f"Using {self.device} device")
        self.model = Properties.get_instance().get_property("llm_model", "ibm-granite/granite-4.0-micro")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model)

        #self.model = AutoModelForCausalLM.from_pretrained(self.model, device_map=self.device)
        self.model = AutoModelForCausalLM.from_pretrained(self.model)
        self.model.eval()

        logging.info("Loading HuggingFaceFace_LLM finished")


    def infuse(self, prompter):
        prompt = prompter.construct_prompt()
        logging.debug("Infusing prompt: " + prompt)
        chat = [
            {"role": "user", "content": prompt},
        ]
        chat = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        # tokenize the text
        input_tokens = self.tokenizer(chat, return_tensors="pt").to(self.device)
        # generate output tokens
        output = self.model.generate(**input_tokens, max_new_tokens=self.max_tokens, temperature=self.temperature)
        # decode output tokens into text
        output = self.tokenizer.batch_decode(output)
        logging.debug("Infuse finished")
        return self.extract_assistant_text(output[0])

    @staticmethod
    def extract_assistant_text(text):
        start = text.find(ASSISTANT_ROLE) + len(ASSISTANT_ROLE)
        end = text.find(END_OF_TEXT, start)
        return text[start:end].strip()