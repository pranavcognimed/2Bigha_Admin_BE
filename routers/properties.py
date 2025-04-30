from fastapi import APIRouter, Depends, HTTPException, status, Form, Response, Request, WebSocket, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.session import get_db_session
from models.properties import Property ,PropertyStatus,Notification
from models.user import User
from fastapi.responses import HTMLResponse
from schemas.properties import PropertyUpdate, PropertyOut, GeoJSONResponse, PaginatedGeoJSONResponse, PropertyStatusCounts, PropertyStatusNotification, UserPropertyResponse
from adminutils.property import convert_properties_to_geojson
from adminutils.auth import get_current_user
from datetime import datetime
from typing import List, Set, Dict
import logging

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.patch("/admin/properties/{property_id}", response_model=PropertyUpdate)
def update_property_status(
    property_id: int,
    property_update: PropertyUpdate,
    db: Session = Depends(get_db_session)
):
    # Retrieve the property from the database
    db_property = db.query(Property).filter(Property.id == property_id).first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update the property's status and flag_reason
    db_property.status = property_update.status
    db_property.flag_reason = property_update.flag_reason
    if property_update.status == "approved":
        db_property.verified = True

    db.commit()
    db.refresh(db_property)
    return db_property

@router.post("/admin/properties/{property_id}/status")
async def update_property_status(
    property_id: int,
    property_update: PropertyUpdate,
    db: Session = Depends(get_db_session)
):
    """
    Update the status of a property and create a notification for the user.
    Admin-only endpoint.
    """

    try:
        # Fetch the property
        db_property = db.query(Property).filter(Property.id == property_id).first()
        if not db_property:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Store old status for comparison
        old_status = db_property.status

        # Update the property's status and flag_reason
        db_property.status = property_update.status
        db_property.flag_reason = property_update.flag_reason
        if property_update.status == "approved":
            db_property.verified = True

        # Create a notification if status changed
        if old_status != property_update.status:
            notification = Notification(
                user_id=db_property.user_id,
                property_id=db_property.id,
                status_change_from=old_status,
                status_change_to=property_update.status,
                created_at=datetime.utcnow()
            )
            db.add(notification)
            logging.info(f"Created notification for property {property_id}: {old_status} -> {property_update.status}")
        
        db.commit()
        db.refresh(db_property)
            
        return {"detail": "Property status updated successfully"}
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating property status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update property status: {str(e)}")

def get_properties_by_status(
    status: PropertyStatus,
    db: Session,
    page: int = 1,
    limit: int = 20
) -> List[Property]:
    """
    Helper function to fetch properties by status with pagination.
    """
    offset = (page - 1) * limit

    # Get total count of properties with the given status
    total_count = db.query(Property).filter(
        Property.status == status
    ).count()

    total_count = int(total_count / limit) + 1

    # Fetch paginated properties, ordered by created_at DESC
    properties = db.query(Property).filter(
         (Property.status == status) & (Property.user_uploaded == True)
    ).order_by(
        Property.created_at.desc()
    ).offset(offset).limit(limit).all()

    if not properties and page == 1:
        raise HTTPException(status_code=404, detail=f"No properties found with status '{status.value}'")

    return properties, total_count

@router.get("/admin/user-properties/counts", response_model=PropertyStatusCounts)
async def get_user_properties_status_counts(
    db: Session = Depends(get_db_session),
):
    """
    Get the count of properties for each status for the current user.
    """
    try:
        # Query to count properties by status for the current user
        status_counts = (
            db.query(Property.status, func.count(Property.id).label("count")).filter(Property.user_uploaded == True)
            .group_by(Property.status)
            .all()
        )

        # Initialize default counts
        counts = {
            "approved": 0,
            "disapproved": 0,
            "flagged": 0,
            "pending": 0,
            "draft": 0
        }

        # Update counts based on query results
        for status, count in status_counts:
            if status in counts:
                counts[status.value] = count

        return PropertyStatusCounts(**counts)

    except Exception as e:
        logging.error(f"Error in get_user_properties_status_counts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve property counts: {str(e)}")

@router.get("/admin/properties/{status}", response_model=PaginatedGeoJSONResponse)
async def get_properties_status(
    status: str,
    page: int = 1,  # Page number, starting from 1
    limit: int = 20,  # Items per page
    db: Session = Depends(get_db_session)
):
    try:
        status_enum = PropertyStatus(status.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {[e.value for e in PropertyStatus]}"
        )

    try:
        # Fetch paginated properties and total count
        properties, total_count = get_properties_by_status(status_enum, db, page, limit)

        # Convert to GeoJSON
        geojson_data = convert_properties_to_geojson(properties)

        # Determine pagination metadata
        has_more = (page * limit) < total_count
        next_page = page + 1 if has_more else None

        return PaginatedGeoJSONResponse(
            data=geojson_data,
            total_count=total_count,
            has_more=has_more,
            next_page=next_page
        )
    except Exception as e:
        db.rollback()  # Rollback in case of any database issues (though rare for GET)
        logging.error(f"Error in get_properties_status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve properties: {str(e)}")