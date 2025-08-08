from langchain_core.prompts import PromptTemplate

PROMPT_TEMPLATE = """
CONTEXT:
{context}

QUESTION:
{question}
"""

rag_prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
