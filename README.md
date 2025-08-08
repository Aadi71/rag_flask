# AI Agent for Academic Q&A (RAG)

This project implements a Retrieval-Augmented Generation (RAG) system to answer questions based on a collection of user-provided academic research papers (PDFs).

The entire system is containerized using Docker and orchestrated with Docker Compose.

## Features

-   **PDF Upload**: Accepts multiple PDF files.
-   **Vectorization**: Extracts text, chunks it, and stores embeddings in **ChromaDB**.
-   **Custom LLM**: Uses a custom **Ollama** model optimized for academic Q&A.
-   **Sourced Answers**: The RAG pipeline retrieves relevant context and generates answers with source citations.
-   **Query Logging**: All interactions are logged in **MongoDB**.
-   **API Documentation**: A **Swagger/OpenAPI** interface is provided for easy interaction.

## How to Run

### Prerequisites

-   Docker and Docker Compose installed.
-   NVIDIA GPU with drivers installed (for hardware acceleration of Ollama). If you don't have a GPU, remove the `deploy` section from the `ollama` service in `docker-compose.yml`.

### 1. Start the Services

From the project's root directory, run the following command:

```bash
docker-compose up --build -d
