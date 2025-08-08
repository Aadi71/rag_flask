from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP
import tempfile
import os

def process_pdfs(pdf_files):
    """
    Extracts text from PDF files, splits it into chunks, and adds metadata.
    """
    all_docs = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    for pdf_file in pdf_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_file.save(tmp.name)
            loader = PyPDFLoader(tmp.name)
            docs = loader.load_and_split(text_splitter=text_splitter)

            # Add the original filename as metadata
            for doc in docs:
                doc.metadata["source_document"] = pdf_file.filename
            all_docs.extend(docs)
        os.remove(tmp.name)
    
    return all_docs
