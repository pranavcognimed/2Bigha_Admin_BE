from fastapi import UploadFile
import json
from passlib.context import CryptContext
from jose import jwt
import random
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import BackgroundTasks, HTTPException, status
from core.config import settings
from typing import List
from jose import jwt
import bcrypt
import smtplib
from sqlalchemy.orm import Session
from typing import List
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import re
import ssl
import os
from models.user import User
from datetime import datetime, timedelta

OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", 300))  # OTP expiry time in seconds (e.g., 5 minutes)

# Optionally, you can configure a custom SSL context
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_CONFIG = {
    "MAIL_USERNAME": settings.MAIL_USERNAME,
    "MAIL_PASSWORD": settings.MAIL_PASSWORD,
    "MAIL_FROM": settings.MAIL_FROM,
    "MAIL_PORT": settings.MAIL_PORT,
    "MAIL_SERVER": settings.MAIL_SERVER,
    "MAIL_STARTTLS":True,        # Replaces MAIL_TLS
    "MAIL_SSL_TLS":False,  
    "USE_CREDENTIALS":True,
    "VALIDATE_CERTS":False
}

# Email configuration
conf = ConnectionConfig(**EMAIL_CONFIG)


def is_valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # at least one uppercase letter
        return False
    if not re.search(r"[a-z]", password):  # at least one lowercase letter
        return False
    if not re.search(r"[0-9]", password):  # at least one digit
        return False
    if not re.search(r"[^a-zA-Z0-9]", password):  # at least one special character
        return False
    return True

def is_valid_username(username: str) -> bool:
    if not re.match(r"^[a-z][a-z0-9_]{2,12}[a-z0-9]$", username):
        return False
    if re.search(r"__+", username):  # no sequence of two or more underscores
        return False
    return True

def is_valid_email(email: str) -> bool:
    # A simple regex for basic email validation
    return re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", email) is not None

def is_valid_phone_number(phone_number: str) -> bool:
    # Checks if the phone number consists only of digits and is between 10 to 15 digits long
    return re.match(r"^\d{10,15}$", phone_number) is not None

def hash_password(password: str) -> str:
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check if the provided password matches the hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def verify_jwt_token(token: str):
    try:
        # Decode the token using the secret key and algorithm
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload  # Return the payload if decoding is successful
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    
# Send email asynchronously
async def send_verification_email(email: str, token: str, background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=f"Your verification token is {token}",
        subtype="plain"
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

def send_email(receiver_email, subject, message):
    # Your email credentials and configuration
    SENDER_EMAIL = "cognimedtech@gmail.com"
    SENDER_NAME = "Cognimed"
    GMAIL_PASSPHRASE = "ajgn fukz ugkc ufju"

    if not SENDER_EMAIL or not GMAIL_PASSPHRASE:
        raise ValueError("Sender email or password is not set in environment variables.")

    try:
        # Create a multipart message
        print(receiver_email)
        msg = MIMEMultipart()
        msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Add message body
        msg.attach(MIMEText(message, 'plain'))

        # Setup the SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Secure the connection
            server.login(SENDER_EMAIL, GMAIL_PASSPHRASE)
            server.send_message(msg)

        print(f"Email sent successfully to {receiver_email}")

    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Recipient refused: {e}")
    except smtplib.SMTPSenderRefused as e:
        print(f"Sender refused: {e}")
    except smtplib.SMTPDataError as e:
        print(f"SMTP data error: {e}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Create JWT token for email verification
def create_jwt_token(data: dict):
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def flatten_user(user_dict: User):
    """
    Flattens a nested user dictionary.
    Args:
        user_dict (dict): The user dictionary to flatten.

    Returns:
        dict: Flattened dictionary.
    """
    # Extract basic user details
    flattened_dict = {
        "user_id": user_dict.user_id,
        "username": user_dict.username,
        "email": user_dict.email,
        "phone_number": user_dict.phone_number,
    }

    # Flatten the profile section if it exists
    profile = user_dict.profile
    flattened_dict.update({
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "college_name": profile.last_name,
    })

    return flattened_dict

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default 15 minutes
    
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt