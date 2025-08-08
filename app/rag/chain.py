# app/rag/chain.py

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, CHROMA_COLLECTION_NAME
from app.rag.prompt_templates import rag_prompt
from app.database.chroma_client import chroma_client
from app.rag.output_parser import output_parser as json_output_parser

# Initialize variables to None
vectorstore = None
rag_chain = None

try:
    # 1. Embeddings Model
    embeddings = OllamaEmbeddings(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL_NAME
    )

    # 2. Vector Store
    vectorstore = Chroma(
        client=chroma_client.client,
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
    )

    # 3. Retriever
    retriever = vectorstore.as_retriever()

    # 4. LLM
    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL_NAME,
        format="json",
        temperature=0
    )

    # 5. RAG Chain
    def format_docs(docs):
        """Prepares the retrieved documents for the prompt."""
        return "\n\n".join(
            f"Source Document: {doc.metadata.get('source_document', 'Unknown')}\n"
            f"Content: {doc.page_content}"
            for doc in docs
        )

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | llm
        | json_output_parser
    )
    print("✅ RAG chain initialized successfully.")

except Exception as e:
    print(f"🔥 FAILED TO INITIALIZE RAG CHAIN AT STARTUP: {e}")
    # This will prevent the app from crashing on import
