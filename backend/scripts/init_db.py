#!/usr/bin/env python3
"""
Database initialization script for BizFindr application.
"""
import os
import sys
import logging
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_mongo_client():
    """Create and return a MongoDB client."""
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/bizfindr')
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

def check_mongodb_connection():
    """Check if MongoDB is accessible."""
    try:
        client = get_mongo_client()
        # The ismaster command is cheap and does not require auth
        client.admin.command('ismaster')
        return True
    except ConnectionFailure:
        return False

def create_indexes(db):
    """Create necessary indexes for collections."""
    try:
        # Create indexes for registrations collection
        db.registrations.create_index([("registration_id", ASCENDING)], unique=True)
        db.registrations.create_index([("business_name", TEXT)])
        db.registrations.create_index([("business_type", ASCENDING)])
        db.registrations.create_index([("date_registration", DESCENDING)])
        db.registrations.create_index([("status", ASCENDING)])
        
        # Create index for fetch_history collection
        db.fetch_history.create_index([("last_fetched_date", DESCENDING)])
        
        logger.info("Database indexes created successfully")
        return True
    except OperationFailure as e:
        logger.error(f"Failed to create indexes: {e}")
        return False

def create_collections(db):
    """Ensure all required collections exist."""
    required_collections = ['registrations', 'fetch_history']
    existing_collections = db.list_collection_names()
    
    for collection in required_collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            logger.info(f"Created collection: {collection}")
        else:
            logger.info(f"Collection already exists: {collection}")

def init_fetch_history(db):
    """Initialize the fetch history if it doesn't exist."""
    if db.fetch_history.count_documents({}) == 0:
        initial_record = {
            "last_fetched_date": None,
            "last_updated": datetime.utcnow(),
            "status": "initialized",
            "records_processed": 0,
            "message": "Initial database setup"
        }
        db.fetch_history.insert_one(initial_record)
        logger.info("Initialized fetch history")

def main():
    """Main function to initialize the database."""
    logger.info("Starting database initialization...")
    
    if not check_mongodb_connection():
        logger.error("Failed to connect to MongoDB. Please check your connection.")
        sys.exit(1)
    
    try:
        client = get_mongo_client()
        db_name = os.getenv('MONGO_DB_NAME', 'bizfindr')
        db = client[db_name]
        
        logger.info(f"Connected to MongoDB: {db_name}")
        
        # Create required collections
        create_collections(db)
        
        # Create indexes
        if not create_indexes(db):
            logger.warning("Some indexes might not have been created")
        
        # Initialize fetch history
        init_fetch_history(db)
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    main()
