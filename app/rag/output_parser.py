from langchain_core.output_parsers import JsonOutputParser
from app.models import AnswerResponse

# The parser expects the LLM to output a JSON string that matches the AnswerResponse model.
# The custom Modelfile instructs the LLM to do this.
output_parser = JsonOutputParser(pydantic_object=AnswerResponse)
