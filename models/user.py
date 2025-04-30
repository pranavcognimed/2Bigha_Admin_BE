from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP, func, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from models import Base, PropertyStatus
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    roles = relationship("UserRoleLink", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    email_verified = Column(Boolean, default=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    active = Column(Boolean, default=True)
    phone_verified = Column(Boolean, default=False)

    user = relationship("User", back_populates="profile")

    
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    user_links = relationship("UserRoleLink", back_populates="role")


class UserRoleLink(Base):
    __tablename__ = "user_role_links"

    # Use the existing columns as composite primary key instead of 'id'
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_links")