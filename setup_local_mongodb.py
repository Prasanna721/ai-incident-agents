#!/usr/bin/env python3
"""
Local MongoDB Setup Script for On-Call Agent

This script helps set up a local MongoDB instance for the on-call agent's shared memory.
It creates the necessary database and collections with proper indexing.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def setup_local_mongodb():
    """Set up local MongoDB for the on-call agent."""
    
    # Default connection string for local MongoDB
    connection_string = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
    database_name = "oncall_swarm"
    collection_name = "incident_memory"
    
    try:
        print("🔧 Setting up local MongoDB for On-Call Agent...")
        print(f"   Connection: {connection_string}")
        print(f"   Database: {database_name}")
        print(f"   Collection: {collection_name}")
        
        # Connect to MongoDB
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        
        # Get database and collection
        db = client[database_name]
        collection = db[collection_name]
        
        # Create indexes for efficient querying
        print("🔍 Creating database indexes...")
        
        # Compound index on session_id and key
        collection.create_index([("session_id", 1), ("key", 1)], unique=True)
        print("   ✓ Created compound index on session_id and key")
        
        # Index on embedding field for vector operations
        collection.create_index([("embedding", 1)])
        print("   ✓ Created index on embedding field")
        
        # Index on timestamp for chronological queries
        collection.create_index([("timestamp", -1)])
        print("   ✓ Created index on timestamp field")
        
        # Insert a test document to verify everything works
        test_doc = {
            "session_id": "setup_test",
            "key": "setup_verification",
            "value": "MongoDB setup successful",
            "timestamp": 1234567890,
            "created_at": "2024-01-01 00:00:00"
        }
        
        collection.insert_one(test_doc)
        print("   ✓ Inserted test document")
        
        # Verify test document can be retrieved
        retrieved = collection.find_one({"session_id": "setup_test"})
        if retrieved:
            print("   ✓ Successfully retrieved test document")
            
            # Clean up test document
            collection.delete_one({"session_id": "setup_test"})
            print("   ✓ Cleaned up test document")
        
        print("\n🎉 MongoDB setup completed successfully!")
        print("\nNext steps:")
        print("1. Make sure your .env file has OPENAI_API_KEY set")
        print("2. Run the on-call agent: python on_call_assistant_swarm.py")
        
        client.close()
        return True
        
    except ConnectionFailure:
        print("❌ Failed to connect to MongoDB")
        print("   Make sure MongoDB is running locally on port 27017")
        print("   Install MongoDB: https://docs.mongodb.com/manual/installation/")
        return False
        
    except ServerSelectionTimeoutError:
        print("❌ Connection timeout to MongoDB")
        print("   Check if MongoDB service is running:")
        print("   - macOS: brew services start mongodb-community")
        print("   - Linux: sudo systemctl start mongod")
        print("   - Windows: net start MongoDB")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error during setup: {e}")
        return False

def check_prerequisites():
    """Check if required packages are installed."""
    required_packages = ['pymongo', 'openai', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 On-Call Agent MongoDB Setup\n")
    
    if not check_prerequisites():
        sys.exit(1)
    
    if setup_local_mongodb():
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)