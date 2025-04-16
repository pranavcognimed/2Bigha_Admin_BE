from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from models.user import User, UserProfile
from db.session import get_db_session
import csv
from io import StringIO
import logging

router = APIRouter()

@router.get("/admin/users/export")
async def export_user_data(db: Session = Depends(get_db_session)):
    """
    Export all user data including profile information as a CSV file.
    """
    try:
        # Query users with their profiles
        users = (
            db.query(User, UserProfile)
            .outerjoin(UserProfile, User.user_id == UserProfile.user_id)
            .all()
        )

        # Prepare CSV in memory
        output = StringIO()
        writer = csv.writer(output, lineterminator='\n')

        # Write CSV headers
        headers = [
            "user_id", "email", "phone_number", "created_at",
            "first_name", "last_name", "active", "email_verified", "phone_verified"
        ]
        writer.writerow(headers)

        # Write user data
        for user, profile in users:
            writer.writerow([
                user.user_id,
                user.email,
                user.phone_number,
                user.created_at.isoformat() if user.created_at else None,
                profile.first_name if profile else None,
                profile.last_name if profile else None,
                profile.active if profile else None,
                profile.email_verified if profile else False,
                profile.phone_verified if profile else False
            ])

        # Reset buffer position
        output.seek(0)

        # Return CSV as a streaming response
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=user_data_export.csv"}
        )

    except Exception as e:
        logging.error(f"Error in export_user_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export user data: {str(e)}")