import os
from typing import Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from prompt_templates import ner_keyword_extractor_template


class NERKeywordExpander:
    """
    Uses an LLM to extract and expand named entities from input text.
    """
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_QUERY_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_QUERY_KEY not set in environment variables")

        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name="gpt-4o",
            temperature=0.0,
            streaming=True
        )

    def query_llm(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns its content response.
        """
        return self.llm.invoke(prompt).content

    def expand(self, text: str) -> str:
        """
        Formats the input using a NER extraction template, queries the LLM,
        and returns the extracted keywords or expanded entities.
        """
        # Prepare prompt with the provided template
        prompt = PromptTemplate(
            input_variables=["input_text"],
            template=ner_keyword_extractor_template
        )

        formatted_prompt = prompt.format(input_text=text)

        # Query the language model
        response = self.query_llm(formatted_prompt)
        return response
