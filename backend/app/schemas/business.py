"""
Pydantic models for business-related data structures.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum


class BusinessCategory(str, Enum):
    """Business categories."""
    RETAIL = "retail"
    FOOD_BEVERAGE = "food_beverage"
    PROFESSIONAL_SERVICES = "professional_services"
    HEALTHCARE = "healthcare"
    CONSTRUCTION = "construction"
    MANUFACTURING = "manufacturing"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class BusinessStatus(str, Enum):
    """Business status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class BusinessBase(BaseModel):
    """Base business model with common fields."""
    name: str = Field(..., max_length=200, description="Legal business name")
    dba: Optional[str] = Field(None, max_length=200, description="Doing Business As name")
    description: Optional[str] = Field(None, description="Business description")
    category: BusinessCategory = Field(..., description="Business category")
    status: BusinessStatus = Field(default=BusinessStatus.ACTIVE, description="Business status")
    
    # Contact information
    email: Optional[str] = Field(None, description="Business email address")
    phone: Optional[str] = Field(None, max_length=20, description="Business phone number")
    website: Optional[HttpUrl] = Field(None, description="Business website URL")
    
    # Location information
    address: str = Field(..., description="Street address")
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=2, description="Two-letter state code")
    zip_code: str = Field(..., max_length=10, description="ZIP or postal code")
    country: str = Field(default="US", max_length=2, description="Two-letter country code")
    
    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Business tags for categorization")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata as key-value pairs"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corp",
                "dba": "Acme",
                "description": "A leading provider of widgets and gadgets",
                "category": "manufacturing",
                "status": "active",
                "email": "info@acme.com",
                "phone": "+1-800-555-1234",
                "website": "https://acme.com",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CT",
                "zip_code": "06001",
                "country": "US",
                "tags": ["wholesale", "retail", "b2b"],
                "metadata": {
                    "founding_year": 1990,
                    "employee_count": 150
                }
            }
        }


class BusinessCreate(BusinessBase):
    """Schema for creating a new business."""
    pass


class BusinessUpdate(BaseModel):
    """Schema for updating an existing business."""
    name: Optional[str] = Field(None, max_length=200)
    dba: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[BusinessCategory] = None
    status: Optional[BusinessStatus] = None
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[HttpUrl] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)
    tags: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "description": "Updated description",
                "status": "active"
            }
        }


class BusinessInDB(BusinessBase):
    """Business model for internal database representation."""
    id: str = Field(..., alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            "datetime": lambda v: v.isoformat()
        }


class Business(BusinessInDB):
    """Business model for API responses."""
    class Config:
        json_encoders = {
            "datetime": lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Acme Corp",
                "dba": "Acme",
                "description": "A leading provider of widgets and gadgets",
                "category": "manufacturing",
                "status": "active",
                "email": "info@acme.com",
                "phone": "+1-800-555-1234",
                "website": "https://acme.com",
                "address": "123 Main St",
                "city": "Anytown",
                "state": "CT",
                "zip_code": "06001",
                "country": "US",
                "tags": ["wholesale", "retail", "b2b"],
                "metadata": {
                    "founding_year": 1990,
                    "employee_count": 150
                },
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
