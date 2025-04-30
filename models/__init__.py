# models/__init__.py
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from .properties import Property, PropertyImage, PropertyStatus
# from .notifications import Notification
from .user import User, UserProfile, Role, UserRoleLink