# app/main.py

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from pydantic import ValidationError
import time
from datetime import datetime
import uuid
import ollama
import sys
import requests

# --- Configuration and Model Imports ---
from app.config import SWAGGER_URL, API_URL, OLLAMA_MODEL_NAME, OLLAMA_BASE_URL
from app.models import QueryRequest, LogEntry, AnswerResponse
from app.utils.pdf_processor import process_pdfs
from app.rag.chain import rag_chain, vectorstore
from app.database.mongo_client import mongo_logger

# --- One-Time Application Setup ---
def ensure_ollama_model_exists():
    """
    Checks if the standard Ollama model exists and pulls it if it doesn't.
    """
    try:
        print("--> [Step 1/2] Checking Ollama server connection...")
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=30)
        response.raise_for_status()
        print("--> [Step 1/2] Ollama server is available.")

        client = ollama.Client(host=OLLAMA_BASE_URL)
        models = client.list().get('models', [])
        
        if any(model['name'] == f"{OLLAMA_MODEL_NAME}" for model in models):
            print(f"--> [Step 2/2] Model '{OLLAMA_MODEL_NAME}' already exists.")
            return

        print(f"--> [Step 2/2] Model '{OLLAMA_MODEL_NAME}' not found. Pulling from Ollama Hub (this may take several minutes)...")
        client.pull(OLLAMA_MODEL_NAME)
        print(f"--> [Step 2/2] ✅ Model '{OLLAMA_MODEL_NAME}' pulled successfully.")

    except Exception as e:
        print(f"🔥 An unexpected error occurred during startup: {e}", file=sys.stderr)
        sys.exit(1)

# Ensure you have a standard model name in app/config.py, like "mistral" or "gemma:2b"
ensure_ollama_model_exists()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Swagger UI Setup ---
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Academic RAG API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# --- API Endpoints ---
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/papers", methods=["POST"])
def upload_papers():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No selected files"}), 400
    try:
        docs = process_pdfs(files)
        if not docs:
            return jsonify({"error": "Could not extract any text from the provided PDFs."}), 400
        doc_ids = [str(uuid.uuid4()) for _ in docs]
        vectorstore.add_documents(documents=docs, ids=doc_ids)
        source_names = sorted(list(set(doc.metadata["source_document"] for doc in docs)))
        return jsonify({
            "status": "success",
            "message": f"Successfully processed and stored {len(docs)} document chunks from {len(source_names)} files.",
            "processed_documents": source_names
        }), 201
    except Exception as e:
        app.logger.error(f"Error processing PDFs: {e}")
        return jsonify({"error": "An internal error occurred while processing the files."}), 500

@app.route("/query", methods=["POST"])
def query_papers():
    start_time = time.time()
    try:
        data = QueryRequest(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    try:
        question = data.question
        if rag_chain is None:
            return jsonify({"error": "RAG chain is not available due to a startup error."}), 503
        result = rag_chain.invoke(question)
        if not isinstance(result, dict) or 'answer' not in result or 'sources' not in result:
             raise TypeError("RAG chain returned an unexpected result format.")
        answer_response = AnswerResponse(**result)
        retrieved_docs = vectorstore.as_retriever().invoke(question)
        retrieved_chunks = [doc.page_content for doc in retrieved_docs]
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            query=question,
            retrieved_chunks=retrieved_chunks,
            generated_answer=answer_response,
            processing_time_ms=processing_time
        )
        mongo_logger.log(log_entry)
        return jsonify(answer_response.dict()), 200
    except Exception as e:
        app.logger.error(f"Error during query processing: {e}")
        return jsonify({"error": f"An internal error occurred: {e}"}), 500

# --- Main Execution ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
