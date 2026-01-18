# CrashGPT - Log Analysis RAG Server

A FastAPI server implementing a Retrieval-Augmented Generation (RAG) pipeline for analyzing system crash logs. This server uses OpenAI embeddings and LLMs combined with Qdrant vector database for intelligent log analysis.

## Architecture

```
User → Upload Logs → FastAPI Server → Qdrant Vector DB
                           ↓
                     RAG Pipeline
                           ↓
                    OpenAI LLM (gpt-4o)
                           ↓
                    Analysis & Answer
```

## Features

- **Log Upload**: Upload crash logs for processing and storage
- **Vector Embeddings**: Automatic embedding of log chunks using OpenAI's text-embedding-3-small
- **Semantic Search**: Retrieve relevant log entries using vector similarity
- **Intelligent Analysis**: Use GPT-4 to generate insights based on retrieved logs
- **Collection Management**: Create, list, and delete vector collections
- **REST API**: Clean, documented API endpoints

## Prerequisites

- Python 3.10+
- OpenAI API key
- Qdrant instance (local or cloud)
- pip or conda for dependency management

## Installation

1. **Clone the repository** (or ensure you have the project files)

2. **Create environment variables** in a `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
QDRANT_API=your_qdrant_api_key_here
QDRANT_ENDPOINT=http://localhost:6333  # or your Qdrant cloud endpoint
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Start Qdrant** (if using local instance):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

## Running the Server

```bash
python server.py
```

The server will start on `http://localhost:8000`

### Using Uvicorn directly:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Endpoints

#### 1. **Health Check**
```
GET /health
```
Check if the server is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-18T10:30:00.123456",
  "service": "CrashGPT RAG Server"
}
```

#### 2. **Upload Logs**
```
POST /upload
```
Upload a log file and process it for RAG.

**Parameters:**
- `file` (form-data): The log file to upload
- `collection_name` (query, optional): Name for the vector collection (default: "mysql_crash_analysis")

**Example:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@mysql_crash_log.txt" \
  -F "collection_name=mysql_crash_analysis"
```

**Response:**
```json
{
  "filename": "mysql_crash_log.txt",
  "collection_name": "mysql_crash_analysis",
  "status": "success",
  "message": "Successfully processed 45 document chunks"
}
```

#### 3. **Query Logs**
```
POST /query
```
Query the vector database using RAG pipeline.

**Request Body:**
```json
{
  "query": "why did my mysql server fail?",
  "collection_name": "mysql_crash_analysis",
  "limit": 6
}
```

**Response:**
```json
{
  "query": "why did my mysql server fail?",
  "answer": "Based on the logs, MySQL failed because: [analysis from LLM]",
  "sources": [
    {
      "content": "Jan 09 13:51:09 deilsy systemd[1]: Starting mysql.service...",
      "score": 0.95,
      "source": "mysql_crash_log.txt"
    }
  ],
  "collection_name": "mysql_crash_analysis"
}
```

#### 4. **List Collections**
```
GET /collections
```
Get all available vector collections.

**Response:**
```json
{
  "collections": [
    {
      "name": "mysql_crash_analysis",
      "vectors_count": 45
    }
  ]
}
```

#### 5. **Get Collection Info**
```
GET /collections/{collection_name}
```
Get detailed information about a specific collection.

**Response:**
```json
{
  "name": "mysql_crash_analysis",
  "vectors_count": 45,
  "status": "green"
}
```

#### 6. **Delete Collection**
```
DELETE /collections/{collection_name}
```
Delete a collection from Qdrant.

**Response:**
```json
{
  "status": "success",
  "message": "Collection 'mysql_crash_analysis' deleted"
}
```

## Usage Example

See [client.py](client.py) for a complete Python client example.

### Quick Python Example:
```python
import requests

BASE_URL = "http://localhost:8000"

# Upload logs
with open("mysql_crash_log.txt", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/upload",
        files=files,
        params={"collection_name": "mysql_crash_analysis"}
    )
    print(response.json())

# Query logs
query_data = {
    "query": "What caused the MySQL server to fail?",
    "collection_name": "mysql_crash_analysis",
    "limit": 6
}
response = requests.post(f"{BASE_URL}/query", json=query_data)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} relevant documents found")
```

## Configuration

### Document Processing
- **chunk_size**: 1000 characters per chunk
- **chunk_overlap**: 200 characters overlap between chunks
- **embedding_model**: text-embedding-3-small
- **llm_model**: gpt-4o
- **llm_temperature**: 0.2 (focused, deterministic responses)

Modify these in `server.py` if needed.

### Vector Database
- **distance_metric**: COSINE similarity
- **batch_size**: 100 points per batch (for upserting)

## Project Structure

```
CrashGPT/
├── server.py              # FastAPI server implementation
├── client.py              # Python client example
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
├── mysql_crash_log.txt    # Sample crash log
├── uploaded_logs/         # Directory for uploaded logs
└── notebook/
    └── document.ipynb     # Jupyter notebook with RAG exploration
```

## How RAG Works

1. **Upload**: User uploads a log file
2. **Processing**: 
   - Load the document
   - Split into overlapping chunks
   - Generate embeddings for each chunk using OpenAI
3. **Storage**: Store chunks and embeddings in Qdrant
4. **Query**:
   - Embed the user's question
   - Search Qdrant for similar log chunks (semantic search)
   - Retrieve top-k relevant chunks
5. **Generation**:
   - Pass retrieved chunks as context to GPT-4
   - GPT-4 analyzes the logs and generates an answer
   - Return structured response with sources

## Troubleshooting

### Qdrant Connection Error
- Ensure Qdrant is running: `docker ps | grep qdrant`
- Check QDRANT_ENDPOINT in `.env`
- Verify network connectivity

### Missing Environment Variables
```
ValueError: Missing required environment variables
```
- Create `.env` file with `OPENAI_API_KEY`, `QDRANT_API`, `QDRANT_ENDPOINT`

### OpenAI API Errors
- Check API key validity
- Verify account has credits
- Check rate limits

### No Documents Found
- Upload logs first using `/upload` endpoint
- Check collection exists: `GET /collections`
- Verify file is not empty

## Performance Tips

1. **Batch uploads**: Process multiple logs in separate collections
2. **Tune chunk size**: Smaller chunks = more specific results, larger chunks = more context
3. **Adjust limit**: Lower limit (3-4) for faster queries, higher (6-10) for more comprehensive context
4. **Use specific queries**: More detailed queries return better results

## Cost Considerations

- **Embeddings**: ~$0.02 per 1M tokens (text-embedding-3-small)
- **LLM**: ~$0.003 per 1K input tokens (gpt-4o with discount)
- **Storage**: Qdrant has free tier with 1M vectors

## License

MIT

## Support

For issues or questions, check the logs or submit an issue to the repository.
