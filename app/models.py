from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    question: str = Field(
        ...,
        min_length=5,
        description="The natural language question to ask the documents."
    )

class Source(BaseModel):
    """Model for a single source citation."""
    document_name: str = Field(..., description="The name of the source PDF document.")
    page_number: int = Field(..., description="The page number within the document.")

class AnswerResponse(BaseModel):
    """Response model for the /query endpoint, structured for clarity."""
    answer: str = Field(..., description="The synthesized answer to the query.")
    sources: List[str] = Field(
        default_factory=list,
        description="A list of unique source document names used to generate the answer."
    )

class LogEntry(BaseModel):
    """Model for logging interactions in MongoDB."""
    timestamp: str
    query: str
    retrieved_chunks: List[str]
    generated_answer: AnswerResponse
    processing_time_ms: float
