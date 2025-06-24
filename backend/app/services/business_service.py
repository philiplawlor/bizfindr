"""
Business service layer with Redis caching.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from pymongo import ReturnDocument
from pymongo.collection import Collection
from bson import ObjectId

from app.core.cache import cache, cached, invalidate_cache
from app.core.config import settings
from app.db.mongodb import get_database
from app.schemas.business import (
    Business, 
    BusinessCreate, 
    BusinessUpdate,
    BusinessInDB
)

logger = logging.getLogger(__name__)

class BusinessService:
    """Service class for business-related operations with Redis caching."""
    
    def __init__(self, db=None):
        """Initialize the business service."""
        self.db = db or get_database()
        self.collection: Collection = self.db["businesses"]
    
    async def _get_business(self, business_id: str) -> Optional[Dict]:
        """Internal method to get a business by ID without caching."""
        try:
            return await self.collection.find_one({"_id": ObjectId(business_id)})
        except Exception as e:
            logger.error(f"Error getting business {business_id}: {e}")
            return None
    
    @cached(timeout=300, key_prefix="business")
    async def get_business(self, business_id: str) -> Optional[BusinessInDB]:
        """
        Get a business by ID with caching.
        
        Args:
            business_id: The business ID to retrieve
            
        Returns:
            BusinessInDB if found, None otherwise
        """
        business = await self._get_business(business_id)
        return BusinessInDB(**business) if business else None
    
    @cached(timeout=60, key_prefix="list_businesses")
    async def list_businesses(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> List[BusinessInDB]:
        """
        List businesses with pagination and optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filter criteria
            
        Returns:
            List of business records
        """
        query = filters or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        return [BusinessInDB(**doc) async for doc in cursor]
    
    async def create_business(self, business: BusinessCreate) -> BusinessInDB:
        """
        Create a new business.
        
        Args:
            business: Business data to create
            
        Returns:
            Created business record
        """
        business_dict = business.dict(exclude_unset=True)
        business_dict["created_at"] = business_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(business_dict)
        created_business = await self._get_business(result.inserted_id)
        
        # Invalidate relevant caches
        await invalidate_cache("list_businesses")
        
        return BusinessInDB(**created_business)
    
    async def update_business(
        self, 
        business_id: str, 
        business_update: BusinessUpdate
    ) -> Optional[BusinessInDB]:
        """
        Update an existing business.
        
        Args:
            business_id: ID of the business to update
            business_update: Updated business data
            
        Returns:
            Updated business record if found, None otherwise
        """
        update_data = business_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(business_id)},
                {"$set": update_data},
                return_document=ReturnDocument.AFTER
            )
            
            if result:
                # Invalidate relevant caches
                await invalidate_cache(f"business:{business_id}")
                await invalidate_cache("list_businesses")
                return BusinessInDB(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error updating business {business_id}: {e}")
            return None
    
    async def delete_business(self, business_id: str) -> bool:
        """
        Delete a business.
        
        Args:
            business_id: ID of the business to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(business_id)})
            if result.deleted_count > 0:
                # Invalidate relevant caches
                await invalidate_cache(f"business:{business_id}")
                await invalidate_cache("list_businesses")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting business {business_id}: {e}")
            return False
    
    @cached(timeout=60, key_prefix="search_businesses")
    async def search_businesses(
        self, 
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[BusinessInDB]:
        """
        Search for businesses by name, description, or other fields.
        
        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching business records
        """
        search_filter = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"dba": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}}
            ]
        }
        
        cursor = self.collection.find(search_filter).skip(skip).limit(limit)
        return [BusinessInDB(**doc) async for doc in cursor]
    
    @cached(timeout=3600, key_prefix="business_statistics")
    async def get_business_statistics(self) -> Dict[str, Any]:
        """
        Get business statistics.
        
        Returns:
            Dictionary containing various business statistics
        """
        # Get total count
        total = await self.collection.count_documents({})
        
        # Count by status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "counts": {"$push": {"status": "$_id", "count": "$count"}}}}
        ]
        
        status_counts = {}
        async for result in self.collection.aggregate(pipeline):
            for item in result.get("counts", []):
                status_counts[item["status"]] = item["count"]
        
        # Count by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_categories = [
            {"category": doc["_id"], "count": doc["count"]} 
            async for doc in self.collection.aggregate(pipeline)
        ]
        
        # Recent activity
        recent_activity = await self.collection.find(
            {},
            {"name": 1, "status": 1, "updated_at": 1}
        ).sort("updated_at", -1).limit(5).to_list(5)
        
        return {
            "total_businesses": total,
            "by_status": status_counts,
            "top_categories": top_categories,
            "recent_activity": recent_activity,
            "timestamp": datetime.utcnow().isoformat()
        }
