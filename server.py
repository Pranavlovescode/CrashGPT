"""
FastAPI server for RAG-based log analysis.
Handles log uploads, storage, and retrieval-augmented generation for crash analysis.
"""

import os
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CrashGPT - Log Analysis RAG Server",
    description="RAG pipeline for analyzing crash logs",
    version="1.0.0"
)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API")
QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT", "http://localhost:6333")
UPLOAD_DIR = Path("./uploaded_logs")

# Validate required environment variables
if not OPENAI_API_KEY or not QDRANT_API_KEY or not QDRANT_ENDPOINT:
    raise ValueError("Missing required environment variables: OPENAI_API_KEY, QDRANT_API, QDRANT_ENDPOINT")

# Create upload directory
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize clients
embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4o",
    temperature=0.2
)

qdrant_client = QdrantClient(url=QDRANT_ENDPOINT)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    collection_name: Optional[str] = "mysql_crash_analysis"
    limit: Optional[int] = 6


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[dict]
    collection_name: str


class UploadResponse(BaseModel):
    filename: str
    collection_name: str
    status: str
    message: str


class CollectionInfo(BaseModel):
    collection_name: str
    document_count: int
    created_at: str


# Helper functions
def setup_collection(collection_name: str) -> int:
    """
    Create a Qdrant collection for storing embeddings.
    Returns the vector size.
    """
    try:
        # Try to delete existing collection to start fresh
        qdrant_client.delete_collection(collection_name)
        logger.info(f"Deleted existing collection: {collection_name}")
    except Exception as e:
        logger.debug(f"Collection {collection_name} doesn't exist or couldn't be deleted: {e}")

    # Get vector size
    vector_size = len(embeddings_model.embed_query("test"))

    # Create collection
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logger.info(f"Created collection: {collection_name} with vector size: {vector_size}")
    return vector_size


def process_and_embed_documents(
    file_path: str,
    collection_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> int:
    """
    Load, split, embed, and store documents in Qdrant.
    Returns the number of documents processed.
    """
    # Load documents
    loader = TextLoader(file_path)
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} documents from {file_path}")

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(split_docs)} chunks")

    # Embed and create points
    points = []
    for idx, doc in enumerate(split_docs):
        embedding = embeddings_model.embed_query(doc.page_content)
        point = PointStruct(
            id=idx,
            vector=embedding,
            payload={
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": file_path
            }
        )
        points.append(point)

    # Upsert points in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        qdrant_client.upsert(collection_name=collection_name, points=batch)
    
    logger.info(f"Upserted {len(points)} embeddings to collection: {collection_name}")
    return len(points)


def retrieve_context(query_text: str, collection_name: str, limit: int = 6) -> list[dict]:
    """
    Retrieve relevant documents from Qdrant vector store.
    """
    query_embedding = embeddings_model.embed_query(query_text)

    response = requests.post(
        f"{QDRANT_ENDPOINT}/collections/{collection_name}/points/search",
        json={
            "vector": query_embedding,
            "limit": limit,
            "with_payload": True
        }
    )

    if response.status_code != 200:
        logger.error(f"Qdrant search failed: {response.text}")
        raise HTTPException(status_code=500, detail="Vector search failed")

    result_data = response.json()
    
    docs = []
    for point in result_data.get("result", []):
        docs.append({
            "content": point["payload"]["content"],
            "score": point["score"],
            "source": point["payload"].get("source", "unknown")
        })

    return docs


def generate_answer(query_text: str, context_docs: list[dict]) -> str:
    """
    Generate an answer using the LLM with retrieved context.
    """
    # Combine context
    context = "\n\n---\n\n".join([doc["content"] for doc in context_docs])

    prompt = f"""You are a Site Reliability Engineer analyzing system crash logs.

TASK: Analyze the provided logs to answer the user's question.

RULES:
1. Extract and report what IS explicitly stated in the logs
2. Identify patterns, timestamps, error codes, and repeated messages
3. For any part you cannot answer from the logs, explicitly state: "Not specified in logs"
4. Be precise and literal - quote exact error messages when relevant

Logs:
{context}

Question: {query_text}

PROVIDE YOUR ANSWER IN THIS FORMAT:

**Observations from Logs:**
- What events occurred (timestamp, service names, error codes)
- Patterns and repetitions
- Key error messages

**Root Cause:**
- What the logs explicitly state as the problem
- If not specified: "Not specified in logs"

**Evidence:**
- Exact log lines that support this analysis
- Line timestamps and full error messages

**Recommended Actions:**
- Based on what the logs suggest
- If no clear solution in logs: "Check /etc/mysql/FROZEN or relevant error file mentioned in logs"

**Prevention:**
- Strategies based on log patterns
- If insufficient: "Not specified in logs"

---"""

    message = HumanMessage(content=prompt)
    response = llm.invoke([message])
    return response.content


# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "CrashGPT RAG Server"
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_log(
    file: UploadFile = File(...),
    collection_name: str = Form("mysql_crash_analysis"),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a log file and process it for RAG.
    
    Args:
        file: The log file to upload
        collection_name: Name of the Qdrant collection to store embeddings
    
    Returns:
        UploadResponse with processing status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved uploaded file: {file_path}")

        # Setup collection
        setup_collection(collection_name)

        # Process documents (can be moved to background task for large files)
        doc_count = process_and_embed_documents(str(file_path), collection_name)

        return UploadResponse(
            filename=file.filename,
            collection_name=collection_name,
            status="success",
            message=f"Successfully processed {doc_count} document chunks"
        )

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_logs(request: QueryRequest):
    """
    Query the log database using RAG pipeline.
    
    Args:
        request: QueryRequest containing the query text
    
    Returns:
        QueryResponse with the generated answer and source documents
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Check if collection exists
        try:
            qdrant_client.get_collection(request.collection_name)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{request.collection_name}' not found. Please upload logs first."
            )

        # Retrieve context
        logger.info(f"Retrieving context for query: {request.query}")
        context_docs = retrieve_context(
            request.query,
            request.collection_name,
            request.limit
        )

        if not context_docs:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found in the vector store"
            )

        # Generate answer
        logger.info("Generating answer using LLM")
        answer = generate_answer(request.query, context_docs)

        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=[
                {
                    "content": doc["content"][:500],
                    "score": doc["score"],
                    "source": doc["source"]
                }
                for doc in context_docs
            ],
            collection_name=request.collection_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/collections")
async def list_collections():
    """List all available Qdrant collections."""
    try:
        collections_response = qdrant_client.get_collections()
        
        # Handle both direct list and nested structure
        collections_list = []
        if hasattr(collections_response, 'collections'):
            collections_list = collections_response.collections
        else:
            collections_list = collections_response
        
        return {
            "collections": [
                {
                    "name": col.name,
                    # "vectors_count": col.vectors_count
                }
                for col in collections_list
            ]
        }
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        # Return empty list instead of error to be more resilient
        return {"collections": []}


@app.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """Get information about a specific collection."""
    try:
        collection_info = qdrant_client.get_collection(collection_name)
        return {
            "name": collection_name,
            "vectors_count": collection_info.vectors_count,
            "status": collection_info.status
        }
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")


@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection from Qdrant."""
    try:
        qdrant_client.delete_collection(collection_name)
        return {"status": "success", "message": f"Collection '{collection_name}' deleted"}
    except Exception as e:
        logger.error(f"Error deleting collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting collection: {str(e)}")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "service": "CrashGPT - Log Analysis RAG Server",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload a log file for analysis",
            "POST /query": "Query the log database",
            "GET /collections": "List all collections",
            "GET /collections/{name}": "Get collection info",
            "DELETE /collections/{name}": "Delete a collection",
            "GET /health": "Health check",
            "GET /": "This endpoint"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
