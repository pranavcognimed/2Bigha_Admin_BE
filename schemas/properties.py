from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, validator
from geoalchemy2.shape import to_shape
from datetime import datetime
from enum import Enum
from geojson import Point
import json

class PropertyStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    disapproved = "disapproved"
    flagged = "flagged"

class PointGeometry(BaseModel):
    type: Literal["Point"]
    coordinates: List[float]  # [longitude, latitude]

    @validator("coordinates")
    def validate_coordinates(cls, v):
        if len(v) != 2:
            raise ValueError("Point coordinates must be [longitude, latitude]")
        return v
    
# PropertyImage Schema
class PropertyImage(BaseModel):
    id: int
    image_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

class PolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: List[List[List[float]]]  # [[[longitude, latitude], ...]]

    @validator("coordinates")
    def validate_polygon_coordinates(cls, v):
        if not v or len(v) < 1 or len(v[0]) < 3:
            raise ValueError("Polygon must have at least one ring with 3+ points")
        for ring in v:
            for point in ring:
                if len(point) != 2:
                    raise ValueError("Each polygon point must be [longitude, latitude]")
        return v

class Properties(BaseModel):
    id: int
    property_name: Optional[str] = Field(None, description="Name of the property")
    owner_name: Optional[str] = Field(None, description="Name of the owner")
    property_type: Optional[str] = Field(None, description="Type of the property")
    price: Optional[float] = Field(None, description="Price of the property")
    area_sq_m: Optional[float] = Field(None, description="Area in square meters")
    unit: Optional[str] = Field(None, description="Unit of area (e.g., Bigha, Acre, Hectare)")
    murabba: Optional[int] = Field(None, description="Murabba number")
    khasra: Optional[str] = Field(None, description="Khasra number")
    khewat: Optional[str] = Field(None, description="Khewat number")
    khata: Optional[str] = Field(None, description="Khata number")
    owner_details_en: Optional[str] = Field(None, description="Owner details in English")
    owner_details_hi: Optional[str] = Field(None, description="Owner details in Hindi")
    state: Optional[str] = Field(None, description="State where the property is located")
    district: Optional[str] = Field(None, description="District/City where the property is located")
    tehsil: Optional[str] = Field(None, description="Tehsil where the property is located")
    village: Optional[str] = Field(None, description="Village/Location where the property is located")
    landmark: Optional[str] = Field(None, description="Landmark near the property")
    verified: Optional[bool] = Field(None, description="Verification status")
    available: Optional[bool] = Field(None, description="Availability status")
    centroid: Optional[PointGeometry] = Field(None, description="Geometric centroid of the property")
    visits: Optional[int] = Field(None, description="Number of visits to the property")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the property was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the property was last updated")
    status: Optional[PropertyStatus] = Field(None, description="Status of the property")
    flag_reason: Optional[str] = Field(None, description="Reason for flagging the property")
    user_uploaded: Optional[bool] = Field(None, description="Whether the property was uploaded by a user")
    phone: Optional[str] = Field(None, description="Phone number of the owner")
    email: Optional[EmailStr] = Field(None, description="Email of the owner")
    # images: List[PropertyImage] = Field(default_factory=list, description="List of property images")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class PropertyUpdate(BaseModel):
    status: PropertyStatus
    flag_reason: Optional[str] = None

class GeoJSONFeature(BaseModel):
    type: Literal["Feature"]
    geometry: PolygonGeometry
    properties: Properties
    images:List[PropertyImage]

class GeoJSONResponse(BaseModel):
    type: Literal["FeatureCollection"]
    features: List[GeoJSONFeature]

class PropertyOut(BaseModel):
    id: int
    property_name: Optional[str] = None
    owner_name: Optional[str] = None
    property_type: Optional[str] = None  # Maps to 'type' in the model
    price: Optional[float] = None
    area_sq_m: Optional[float] = None
    unit: Optional[str] = None
    murabba: Optional[int] = None
    khasra: Optional[str] = None
    khewat: Optional[str] = None
    khata: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    tehsil: Optional[str] = None
    village: Optional[str] = None
    landmark: Optional[str] = None
    verified: Optional[bool] = None
    available: Optional[bool] = None
    centroid: Optional[PointGeometry] = None
    geom: PolygonGeometry
    visits: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[PropertyStatus] = None
    user_uploaded: Optional[bool] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    images: List[PropertyImage] = []

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class PaginatedGeoJSONResponse(BaseModel):
    data: GeoJSONResponse  # GeoJSON data for the current page
    total_count: int  # Total number of properties
    has_more: bool  # Whether more pages exist
    next_page: Optional[int]  # Next page number, if applicable

    class Config:
        orm_mode = True

class PropertyStatusCounts(BaseModel):
    approved: int = Field(..., description="Number of approved properties")
    disapproved: int = Field(..., description="Number of disapproved properties")
    flagged: int = Field(..., description="Number of flagged properties")
    pending: int = Field(..., description="Number of pending properties")
    draft: int = Field(..., description="Number of draft properties")