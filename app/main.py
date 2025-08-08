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


def wait_for_ollama(max_retries=30, delay=5):
    """Wait until Ollama API is ready."""
    print(f"Attempting to connect to Ollama at {OLLAMA_BASE_URL}")
    for attempt in range(max_retries):
        try:
            print(f"--> Checking Ollama API (attempt {attempt+1}/{max_retries})...")
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
            if response.status_code == 200:
                print("--> ✅ Ollama API is up and responding.")
                return True
        except Exception as e:
            print(f"--> Connection attempt failed: {str(e)}")
        time.sleep(delay)
    print("❌ Ollama API did not become ready in time.")
    return False

# In app/main.py, replace the entire startup function

def create_ollama_model_if_not_exists():
    wait_for_ollama()
    """
    Checks if the Ollama server is responsive and creates the custom model if it doesn't exist.
    """
    try:
        print("--> [Step 1/2] Connecting to Ollama server...")
        # Use the robust 'requests' library for the initial check.
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=30)
        response.raise_for_status()
        print("--> [Step 1/2] Ollama server is available.")

        # Now, connect using the ollama client.
        client = ollama.Client(host=OLLAMA_BASE_URL)
        models = client.list().get('models', [])
        print(f"--> [Step 2/2] Found {len(models)} models on the Ollama server.")
        
        if any(model['name'] == f"{OLLAMA_MODEL_NAME}:latest" for model in models):
            print(f"--> [Step 2/2] Model '{OLLAMA_MODEL_NAME}' already exists. Setup complete.")
            return

        print(f"--> [Step 2/2] Model '{OLLAMA_MODEL_NAME}' not found. Creating from Modelfile...")
        # with open("/modelfile/Modelfile", "r") as f:
        #     modelfile_content = f.read()
            # print(f"Modelfile content:\n{modelfile_content}")
        
        ollama.create(model=OLLAMA_MODEL_NAME, from_='llama3', system="""
            You are an expert AI assistant specialized in answering questions based on academic research papers.
            Your task is to synthesize information from the provided text excerpts and deliver a clear, concise, and accurate answer.
            Follow these rules strictly:
            1.  Base your answer ONLY on the information given in the 'CONTEXT' section. Do not use any external knowledge.
            2.  If the context does not contain the answer, state clearly: "Based on the provided documents, I cannot answer this question."
            3.  You must cite the sources you used to construct your answer. The sources are provided in the context with metadata like 'source_document'.
            4.  Structure your response as a JSON object with two keys: 'answer' and 'sources'.
                - The 'answer' should be a string containing your synthesized response.
                - The 'sources' should be an array of strings, listing the unique 'source_document' names you used.
        """
        )
        
        print(f"--> [Step 2/2] ✅ Model '{OLLAMA_MODEL_NAME}' created successfully. Setup complete.")

    except Exception as e:
        print(f"🔥 An unexpected error occurred during startup: {e}", file=sys.stderr)
        sys.exit(1)

# Run the setup function once when the application starts
create_ollama_model_if_not_exists()


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
    """A simple landing page."""
    return render_template('index.html')

@app.route("/papers", methods=["POST"])
def upload_papers():
    """Endpoint to upload multiple PDF research papers."""
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
    """Endpoint to ask a question about the uploaded papers."""
    start_time = time.time()
    try:
        data = QueryRequest(**request.json)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    try:
        question = data.question
        result = rag_chain.invoke(question)
        
        # Ensure result is in the correct format before logging
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
            generated_answer=answer_response, # Use the validated Pydantic model
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
