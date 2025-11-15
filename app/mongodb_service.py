import logging
from typing import Optional, Dict, Any
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, PyMongoError
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for interacting with MongoDB for email tracking data"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Initialize MongoDB connection"""
        try:
            if not settings.mongodb_connection_string:
                logger.warning("MongoDB connection string not provided. Tracking features will be unavailable.")
                return
            
            self.client = MongoClient(
                settings.mongodb_connection_string,
                server_api=ServerApi('1')
            )
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
            # Get database and collection
            self.db = self.client[settings.mongodb_database]
            self.collection = self.db[settings.mongodb_collection]
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing MongoDB connection: {e}")
            self.client = None
    
    def get_tracking_data(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking data for a message ID (UUID)
        
        Args:
            message_id: The UUID of the message to get tracking data for
            
        Returns:
            Dictionary containing tracking data or None if not found
        """
        if self.collection is None:
            logger.error("MongoDB collection not available")
            return None
        
        try:
            # Query by UUID field
            document = self.collection.find_one({"uuid": message_id})
            
            if not document:
                logger.info(f"No tracking data found for message ID: {message_id}")
                return None
            
            # Convert ObjectId to string and handle date objects
            result = {
                "_id": str(document.get("_id", "")),
                "uuid": document.get("uuid"),
                "createdAt": document.get("createdAt"),
                "views": []
            }
            
            # Process views array
            views = document.get("views", [])
            for view in views:
                view_data = {
                    "timestamp": view.get("timestamp"),
                    "ip": view.get("ip"),
                    "userAgent": view.get("userAgent"),
                    "referrer": view.get("referrer"),
                    "browser": view.get("browser"),
                    "device": view.get("device"),
                    "os": view.get("os"),
                    "location": view.get("location")
                }
                result["views"].append(view_data)
            
            return result
            
        except PyMongoError as e:
            logger.error(f"MongoDB error getting tracking data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting tracking data: {e}")
            return None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# Global MongoDB service instance
mongodb_service = MongoDBService()

