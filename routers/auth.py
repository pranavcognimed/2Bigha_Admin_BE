from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Form, status, Response
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random
import os
from dotenv import load_dotenv
from jose import jwt, JWTError, ExpiredSignatureError
from models.user import User, UserProfile, UserRoleLink
import sqlalchemy as sa
from sqlalchemy import text
from schemas.user import Token
from db.session import get_db_session
from utils.auth import (
    hash_password,
    create_jwt_token,
    create_access_token,
    verify_jwt_token,
    send_email,
    verify_password,
    is_valid_email,
    is_valid_password,
    is_valid_username,
    is_valid_phone_number
)

ACCESS_TOKEN_EXPIRE_MINUTES = 360
REFRESH_TOKEN_EXPIRE_DAYS = 30
# Load environment variables from a .env file if it exists
load_dotenv()

# Secret key for JWT token signing (ensure this is kept safe and secret)
SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")

router = APIRouter()
@router.post("/admin/signup", status_code=status.HTTP_201_CREATED)
async def admin_signup(
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db_session),
    background_tasks: BackgroundTasks = None
):
    if not is_valid_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long, contain at least one uppercase, one lowercase, one digit, and one special character."
        )

    if not is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Check if user already exists
    user_in_db = db.query(User).filter(User.email == email).first()
    if user_in_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already registered with this email"
        )

    hashed_password = hash_password(password)

    # Email verification link
    email_verification_token = create_jwt_token({"email": email})
    verification_link = f"http://localhost:8000/auth/verify-email?token={email_verification_token}"
    background_tasks.add_task(send_email, email, "Verification Mail", verification_link)

    try:
        # Create User and Profile
        new_user = User(email=email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create profile
        new_profile = UserProfile(user_id=new_user.user_id, email_verified=False)
        db.add(new_profile)

        # Assign Admin role (role_id=0 for admin)
        admin_role_link = UserRoleLink(user_id=new_user.user_id, role_id=0)  # Changed from 2 to 0
        db.add(admin_role_link)
        
        # Commit both profile and role assignment
        db.commit()
        
        return {"message": "Admin account created. Please verify your email to activate your account."}
        
    except Exception as e:
        db.rollback()
        # If we've already created the user but subsequent operations failed,
        # clean up by deleting the user
        if 'new_user' in locals() and hasattr(new_user, 'user_id'):
            db.query(User).filter(User.user_id == new_user.user_id).delete()
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin account: {str(e)}"
        )

# @router.post("/admin/login", response_model=Token)
# async def login(
#     response: Response,
#     identifier: str = Form(...),
#     password: str = Form(...),
#     db: Session = Depends(get_db_session)
# ):
#     # Use raw SQL query to fetch user_id and hashed_password
#     user_query = sa.text("""
#         SELECT user_id, hashed_password FROM users WHERE email=:identifier
#     """)
#     user = db.execute(user_query, {"identifier": identifier}).fetchone()
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     user_id, hashed_password = user
#     # Verify the password
#     if not verify_password(password, hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect password"
#         )
    
#     # Fetch user role
#     role_query = sa.text("SELECT role_id FROM user_role_links WHERE user_id = :user_id")
#     role = db.execute(role_query, {'user_id': user_id}).fetchone()
    
#     if not role:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User role not found"
#         )
    
#     role_id = role[0]

#     # Create access token and refresh token
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

#     access_token = create_access_token(
#         data={
#             "sub": identifier,
#             "user_id": user_id,
#             "role": role_id
#         },
#         expires_delta=access_token_expires
#     )
#     refresh_token = create_access_token(
#         data={
#             "sub": identifier,
#             "user_id": user_id,
#             "role": role_id
#         },
#         expires_delta=refresh_token_expires
#     )

#     # Set refresh token in an HttpOnly, Secure cookie
#     response.set_cookie(
#         key="refresh_token",
#         value=refresh_token,
#         httponly=True,    # HttpOnly: not accessible via JavaScript
#         secure=True,      # Secure: only sent over HTTPS
#         samesite="Strict",  # 'Strict' or 'Lax' depending on your needs
#         max_age=int(refresh_token_expires.total_seconds())
#     )
    
#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }
    
@router.post("/admin/login", response_model=Token)
async def admin_login(
    response: Response,
    identifier: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_session)
):
    # Find user by email using the ORM
    user = db.query(User).filter(User.email == identifier).first()

    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Fetch role using the ORM
    user_role = db.query(UserRoleLink).filter(UserRoleLink.user_id == user.user_id).first()

    if not user_role:
        raise HTTPException(status_code=401, detail="User role not found")

    # Check if the user has the admin role (role_id = 0)
    if user_role.role_id != 0:  # Changed from 2 to 0
        raise HTTPException(status_code=403, detail="Not authorized as admin")

    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": identifier, "user_id": user.user_id, "role": user_role.role_id},
        expires_delta=access_token_expires
    )

    refresh_token = create_access_token(
        data={"sub": identifier, "user_id": user.user_id, "role": user_role.role_id},
        expires_delta=refresh_token_expires
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=int(refresh_token_expires.total_seconds())
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }