#!/usr/bin/env python3
"""
MongoDB Atlas Shared Memory Implementation

A shared memory system using MongoDB Atlas Vector Search with OpenAI embeddings
for the finance assistant swarm agents.
"""

import os
import time
from typing import Dict, Any, List, Optional
import hashlib
import json

# Third-party imports
import pymongo
from pymongo import MongoClient
from openai import OpenAI
import numpy as np

class MongoDBAtlasSharedMemory:
    """
    MongoDB Atlas-based shared memory with vector search capabilities.
    Uses OpenAI embeddings for semantic search and storage.
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 database_name: str = "oncall_swarm",
                 collection_name: str = "incident_memory",
                 openai_api_key: Optional[str] = None):
        """
        Initialize MongoDB Atlas shared memory.
        
        Args:
            connection_string: MongoDB Atlas connection string
            database_name: Database name for shared memory
            collection_name: Collection name for shared memory
            openai_api_key: OpenAI API key for embeddings
        """
        
        # Get credentials from environment if not provided
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.connection_string:
            raise ValueError("MongoDB connection string is required. Set MONGODB_CONNECTION_STRING environment variable or use default localhost.")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize clients
        self.client = MongoClient(self.connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Session ID for this swarm instance
        self.session_id = self._generate_session_id()
        
        # Create indexes if they don't exist
        self._ensure_indexes()
        
        print(f"MongoDB Shared Memory initialized with session: {self.session_id}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for this swarm instance."""
        timestamp = str(int(time.time()))
        random_hash = hashlib.md5(f"{timestamp}_{os.getpid()}".encode()).hexdigest()[:8]
        return f"session_{timestamp}_{random_hash}"
    
    def _ensure_indexes(self):
        """Ensure required indexes exist for efficient querying."""
        try:
            # Create compound index on session_id and key
            self.collection.create_index([("session_id", 1), ("key", 1)], unique=True)
            
            # Create vector search index (this needs to be done in Atlas UI or via API)
            # For now, we'll create a regular index on embeddings
            self.collection.create_index([("embedding", 1)])
            
            print("Database indexes ensured")
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        Get OpenAI embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Use text-embedding-3-small for efficiency
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def store(self, key: str, value: Any) -> bool:
        """
        Store a key-value pair in shared memory with vector embedding.
        
        Args:
            key: Storage key
            value: Value to store (will be JSON serialized)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize value to JSON string
            if isinstance(value, str):
                serialized_value = value
            else:
                serialized_value = json.dumps(value, default=str)
            
            # Generate embedding for the value
            embedding = self._get_embedding(f"{key}: {serialized_value}")
            
            # Create document
            document = {
                "session_id": self.session_id,
                "key": key,
                "value": serialized_value,
                "original_type": type(value).__name__,
                "embedding": embedding,
                "timestamp": time.time(),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Upsert document (replace if exists)
            self.collection.replace_one(
                {"session_id": self.session_id, "key": key},
                document,
                upsert=True
            )
            
            print(f"Stored key '{key}' in shared memory")
            return True
            
        except Exception as e:
            print(f"Error storing key '{key}': {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key from shared memory.
        
        Args:
            key: Storage key
            
        Returns:
            Retrieved value or None if not found
        """
        try:
            document = self.collection.find_one({
                "session_id": self.session_id,
                "key": key
            })
            
            if not document:
                return None
            
            # Try to deserialize based on original type
            value = document["value"]
            original_type = document.get("original_type", "str")
            
            if original_type == "str":
                return value
            else:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
                    
        except Exception as e:
            print(f"Error retrieving key '{key}': {e}")
            return None
    
    def get_all_knowledge(self) -> Dict[str, Any]:
        """
        Retrieve all stored knowledge from shared memory.
        
        Returns:
            Dictionary of all key-value pairs
        """
        try:
            documents = self.collection.find({"session_id": self.session_id})
            knowledge = {}
            
            for doc in documents:
                key = doc["key"]
                value = doc["value"]
                original_type = doc.get("original_type", "str")
                
                # Deserialize value
                if original_type == "str":
                    knowledge[key] = value
                else:
                    try:
                        knowledge[key] = json.loads(value)
                    except json.JSONDecodeError:
                        knowledge[key] = value
            
            print(f"Retrieved {len(knowledge)} items from shared memory")
            return knowledge
            
        except Exception as e:
            print(f"Error retrieving all knowledge: {e}")
            return {}
    
    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of similar documents with similarity scores
        """
        try:
            # Get embedding for query
            query_embedding = self._get_embedding(query)
            
            if not query_embedding:
                return []
            
            # For now, use basic retrieval since Atlas Vector Search requires special setup
            # In production, you would use Atlas Vector Search aggregation pipeline
            documents = list(self.collection.find({"session_id": self.session_id}))
            
            # Calculate cosine similarity
            results = []
            for doc in documents:
                if "embedding" in doc and doc["embedding"]:
                    doc_embedding = doc["embedding"]
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    
                    results.append({
                        "key": doc["key"],
                        "value": doc["value"],
                        "similarity": similarity,
                        "timestamp": doc["timestamp"]
                    })
            
            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f"Error searching similar content: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            a_np = np.array(a)
            b_np = np.array(b)
            return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))
        except Exception:
            return 0.0
    
    def clear_session(self) -> bool:
        """
        Clear all data for current session.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.delete_many({"session_id": self.session_id})
            print(f"Cleared {result.deleted_count} items from shared memory")
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
    
    def list_keys(self) -> List[str]:
        """
        List all keys in shared memory for current session.
        
        Returns:
            List of keys
        """
        try:
            documents = self.collection.find(
                {"session_id": self.session_id}, 
                {"key": 1, "_id": 0}
            )
            return [doc["key"] for doc in documents]
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if hasattr(self, 'client'):
            self.client.close()
            print("MongoDB connection closed")


# Factory function to create shared memory instance
def create_shared_memory() -> MongoDBAtlasSharedMemory:
    """
    Factory function to create a shared memory instance.
    Reads configuration from environment variables.
    
    Environment Variables:
        MONGODB_CONNECTION_STRING: MongoDB connection string (defaults to localhost:27017)
        OPENAI_API_KEY: OpenAI API key
    
    Returns:
        MongoDBAtlasSharedMemory instance
    """
    return MongoDBAtlasSharedMemory()


# Example usage and testing
if __name__ == "__main__":
    # Test the shared memory implementation
    try:
        # Create shared memory instance
        shared_memory = create_shared_memory()
        
        # Test storing data
        shared_memory.store("query", "AAPL stock analysis")
        shared_memory.store("ticker", "AAPL")
        shared_memory.store("analysis_data", {"price": 150.0, "change": 2.5})
        
        # Test retrieval
        print("\nTesting retrieval:")
        print(f"Query: {shared_memory.get('query')}")
        print(f"Ticker: {shared_memory.get('ticker')}")
        print(f"Analysis data: {shared_memory.get('analysis_data')}")
        
        # Test get_all_knowledge
        print("\nAll knowledge:")
        all_data = shared_memory.get_all_knowledge()
        for key, value in all_data.items():
            print(f"  {key}: {value}")
        
        # Test similarity search
        print("\nSimilarity search for 'stock price':")
        similar = shared_memory.search_similar("stock price", limit=3)
        for item in similar:
            print(f"  {item['key']}: {item['similarity']:.3f}")
        
        # Clean up
        shared_memory.close()
        
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure to set MONGODB_CONNECTION_STRING and OPENAI_API_KEY environment variables")