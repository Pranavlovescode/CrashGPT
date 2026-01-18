"""
Python client for CrashGPT RAG Server.
Demonstrates how to interact with the log analysis API.
"""

import requests
import json
from typing import Optional
from pathlib import Path

class CrashGPTClient:
    """Client for interacting with CrashGPT RAG server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the CrashGPT server
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """Check if the server is healthy."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def upload_log(
        self,
        file_path: str,
        collection_name: str = "mysql_crash_analysis"
    ) -> dict:
        """
        Upload a log file for processing.
        
        Args:
            file_path: Path to the log file
            collection_name: Name for the vector collection
        
        Returns:
            Response data with upload status
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            params = {"collection_name": collection_name}
            response = self.session.post(
                f"{self.base_url}/upload",
                files=files,
                params=params
            )
        
        response.raise_for_status()
        return response.json()
    
    def query(
        self,
        query_text: str,
        collection_name: str = "mysql_crash_analysis",
        limit: int = 6
    ) -> dict:
        """
        Query the log database.
        
        Args:
            query_text: The question to ask
            collection_name: Name of the collection to query
            limit: Number of source documents to retrieve
        
        Returns:
            Response data with answer and sources
        """
        payload = {
            "query": query_text,
            "collection_name": collection_name,
            "limit": limit
        }
        
        response = self.session.post(
            f"{self.base_url}/query",
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def list_collections(self) -> list:
        """Get list of all collections."""
        response = self.session.get(f"{self.base_url}/collections")
        response.raise_for_status()
        data = response.json()
        return data.get("collections", [])
    
    def get_collection_info(self, collection_name: str) -> dict:
        """Get information about a specific collection."""
        response = self.session.get(
            f"{self.base_url}/collections/{collection_name}"
        )
        response.raise_for_status()
        return response.json()
    
    def delete_collection(self, collection_name: str) -> dict:
        """Delete a collection."""
        response = self.session.delete(
            f"{self.base_url}/collections/{collection_name}"
        )
        response.raise_for_status()
        return response.json()


def main():
    """Demonstration of the CrashGPT client."""
    
    # Initialize client
    client = CrashGPTClient("http://localhost:8000")
    
    print("=" * 60)
    print("CrashGPT Client Demo")
    print("=" * 60)
    
    # Check health
    print("\n1. Health Check")
    print("-" * 60)
    try:
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"Service: {health['service']}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the server is running: python server.py")
        return
    
    # Upload logs
    print("\n2. Upload Log File")
    print("-" * 60)
    try:
        result = client.upload_log(
            "mysql_crash_log.txt",
            collection_name="mysql_crash_analysis"
        )
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Collection: {result['collection_name']}")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return
    
    # List collections
    print("\n3. List Collections")
    print("-" * 60)
    try:
        collections = client.list_collections()
        for col in collections:
            print(f"- {col['name']}: {col['vectors_count']} vectors")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get collection info
    print("\n4. Collection Information")
    print("-" * 60)
    try:
        info = client.get_collection_info("mysql_crash_analysis")
        print(f"Name: {info['name']}")
        print(f"Vector Count: {info['vectors_count']}")
        print(f"Status: {info['status']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Query examples
    queries = [
        "Why did my MySQL server fail?",
        "What caused the service to crash?",
        "How can I prevent this error in the future?",
        "What is the root cause of the failure?"
    ]
    
    print("\n5. RAG Queries")
    print("-" * 60)
    
    for i, query_text in enumerate(queries, 1):
        print(f"\nQuery {i}: {query_text}")
        print("." * 60)
        
        try:
            result = client.query(
                query_text,
                collection_name="mysql_crash_analysis",
                limit=6
            )
            
            print(f"\nAnswer:\n{result['answer']}")
            
            print(f"\nRelevant Sources ({len(result['sources'])} found):")
            for j, source in enumerate(result['sources'][:2], 1):  # Show top 2
                print(f"  Source {j} (Score: {source['score']:.4f}):")
                print(f"  {source['content'][:150]}...")
        
        except Exception as e:
            print(f"Error: {e}")
        
        print()
    
    # Cleanup option
    print("\n6. Cleanup (Optional)")
    print("-" * 60)
    try:
        response = input("Delete collection? (y/n): ")
        if response.lower() == 'y':
            result = client.delete_collection("mysql_crash_analysis")
            print(f"Result: {result['message']}")
    except KeyboardInterrupt:
        print("Skipped")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
