"""
API v1 router configuration.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.core.cache import cached
from app.core.config import settings
from app.schemas.business import Business, BusinessCreate, BusinessUpdate
from app.services.business_service import BusinessService

# Create API router
api_router = APIRouter()

# Business endpoints
@api_router.get("/businesses/", response_model=List[Business])
@cached(timeout=300, key_prefix="list_businesses")
async def list_businesses(
    skip: int = 0,
    limit: int = 100,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Retrieve a list of businesses with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of business records
    """
    return await business_service.list_businesses(skip=skip, limit=limit)


@api_router.get("/businesses/{business_id}", response_model=Business)
@cached(timeout=300, key_prefix="get_business")
async def get_business(
    business_id: str,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Retrieve a single business by ID.
    
    Args:
        business_id: ID of the business to retrieve
        
    Returns:
        Business record if found
        
    Raises:
        HTTPException: If business is not found
    """
    business = await business_service.get_business(business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found"
        )
    return business


@api_router.post("/businesses/", response_model=Business, status_code=status.HTTP_201_CREATED)
async def create_business(
    business: BusinessCreate,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Create a new business.
    
    Args:
        business: Business data to create
        
    Returns:
        Created business record
    """
    return await business_service.create_business(business)


@api_router.put("/businesses/{business_id}", response_model=Business)
async def update_business(
    business_id: str,
    business_update: BusinessUpdate,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Update an existing business.
    
    Args:
        business_id: ID of the business to update
        business_update: Updated business data
        
    Returns:
        Updated business record
        
    Raises:
        HTTPException: If business is not found
    """
    updated_business = await business_service.update_business(business_id, business_update)
    if not updated_business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found"
        )
    return updated_business


@api_router.delete("/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Delete a business.
    
    Args:
        business_id: ID of the business to delete
        
    Returns:
        No content on success
        
    Raises:
        HTTPException: If business is not found
    """
    success = await business_service.delete_business(business_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business with ID {business_id} not found"
        )
    return None


# Search endpoint
@api_router.get("/search/", response_model=List[Business])
@cached(timeout=300, key_prefix="search_businesses")
async def search_businesses(
    query: str,
    skip: int = 0,
    limit: int = 100,
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Search for businesses by name, description, or other fields.
    
    Args:
        query: Search query string
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of matching business records
    """
    return await business_service.search_businesses(query, skip=skip, limit=limit)


# Statistics endpoint
@api_router.get("/statistics/")
@cached(timeout=3600, key_prefix="get_business_statistics")
async def get_business_statistics(
    business_service: BusinessService = Depends(BusinessService)
):
    """
    Get business statistics.
    
    Returns:
        Dictionary containing various business statistics
    """
    return await business_service.get_business_statistics()
