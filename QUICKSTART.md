# Quick Start Guide

Get your CrashGPT RAG server up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- Docker (for Qdrant) or existing Qdrant instance
- OpenAI API key from https://platform.openai.com/api-keys

## Step 1: Setup Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-key-here
QDRANT_API=your-qdrant-api-key
QDRANT_ENDPOINT=http://localhost:6333
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Start Qdrant (Local)

```bash
docker run -d -p 6333:6333 \
  -e QDRANT_API_KEY=your-qdrant-api-key \
  qdrant/qdrant:latest
```

Or use Qdrant Cloud and update `QDRANT_ENDPOINT` in `.env`.

## Step 4: Start the Server

```bash
python server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Test the API

### Option A: Using Python Client

```bash
python client.py
```

This will:
1. Check server health
2. Upload `mysql_crash_log.txt`
3. List collections
4. Run multiple queries
5. Display results

### Option B: Using curl

```bash
# Health check
curl http://localhost:8000/health

# Upload log
curl -X POST http://localhost:8000/upload \
  -F "file=@mysql_crash_log.txt"

# Query logs
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why did MySQL fail?",
    "collection_name": "mysql_crash_analysis",
    "limit": 6
  }'
```

### Option C: Interactive API Docs

Open http://localhost:8000/docs in your browser for Swagger UI.

## Common Issues

### Error: "OPENAI_API_KEY not found"
- Create `.env` file with your OpenAI key
- Restart the server

### Error: "Cannot connect to Qdrant"
- Check Qdrant is running: `docker ps`
- Verify `QDRANT_ENDPOINT` in `.env`
- Start Qdrant: `docker run -d -p 6333:6333 qdrant/qdrant`

### Error: "Collection not found"
- Upload logs first via `/upload` endpoint
- Check collection name matches

## Next Steps

1. **Modify queries**: Edit the queries in `client.py` for your use case
2. **Upload your logs**: Use the `/upload` endpoint with your own log files
3. **Adjust parameters**: Tune chunk_size, temperature, etc. in `server.py`
4. **Deploy**: Use Gunicorn or Uvicorn for production

## Production Deployment

### Using Uvicorn with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t crashgpt-server .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxx \
  -e QDRANT_API=xxx \
  -e QDRANT_ENDPOINT=http://qdrant:6333 \
  crashgpt-server
```

## Architecture Diagram

```
┌──────────────┐
│   User       │
│   (Browser   │
│   / Client)  │
└──────┬───────┘
       │
       │ HTTP REST API
       ↓
┌──────────────────────────────────┐
│     FastAPI Server               │
│  ┌──────────────────────────────┐│
│  │ Upload Endpoint              ││
│  │ - File handling              ││
│  │ - Document loading           ││
│  │ - Chunking (1000 chars)      ││
│  └──────────┬───────────────────┘│
│             ↓                     │
│  ┌──────────────────────────────┐│
│  │ Embedding Pipeline           ││
│  │ - OpenAI text-embedding-3    ││
│  │ - Generate vectors for each  ││
│  │   chunk                      ││
│  └──────────┬───────────────────┘│
│             ↓                     │
│  ┌──────────────────────────────┐│
│  │ Qdrant Storage               ││
│  │ - Store vectors & chunks     ││
│  │ - COSINE similarity metric   ││
│  └──────────────────────────────┘│
│                                  │
│  ┌──────────────────────────────┐│
│  │ Query Endpoint               ││
│  │ - Embed user query           ││
│  │ - Vector search in Qdrant    ││
│  │ - Retrieve top-k chunks      ││
│  └──────────┬───────────────────┘│
│             ↓                     │
│  ┌──────────────────────────────┐│
│  │ LLM Pipeline (gpt-4o)        ││
│  │ - System prompt              ││
│  │ - Retrieved context          ││
│  │ - User query                 ││
│  │ - Generate answer            ││
│  └──────────┬───────────────────┘│
│             ↓                     │
└──────────────────────────────────┘
       │
       │ JSON Response
       ↓
    Answer + Sources
```

## API Response Example

```json
{
  "query": "Why did MySQL fail?",
  "answer": "Based on the logs, MySQL failed because:
    - Root Cause: The systemd service encountered an exit status 1/FAILURE
    - Evidence: Multiple log entries show 'mysql.service: Control process exited, code=exited, status=1/FAILURE'
    - Recommended Fix: Check /etc/mysql/FROZEN for the specific issue. The logs indicate 'MySQL has been frozen to prevent damage to your system'
    - Prevention: Monitor service health and implement automated recovery mechanisms",
  "sources": [
    {
      "content": "Jan 09 13:51:09 deilsy systemd[1]: mysql.service: Control process exited...",
      "score": 0.95,
      "source": "mysql_crash_log.txt"
    }
  ],
  "collection_name": "mysql_crash_analysis"
}
```

## Performance Metrics

- **Upload**: ~2-5 seconds for typical log file
- **Embedding**: ~0.1s per chunk (parallelized in batches)
- **Vector Search**: ~50-100ms
- **LLM Response**: ~1-3 seconds
- **Total Query Time**: ~2-5 seconds

## Monitoring

Check logs in real-time:

```bash
# Server logs (if running with --reload)
# Look for INFO level messages

# Monitor vector DB size
curl http://localhost:6333/health

# Check collections
curl http://localhost:8000/collections
```

---

**Ready to go!** Start with `python client.py` and modify as needed for your use case.
