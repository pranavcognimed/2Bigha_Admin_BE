from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, Enum,
    TIMESTAMP, DECIMAL, ForeignKey, Identity, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, backref
from geoalchemy2 import Geography
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class PropertyStatus(str, enum.Enum):  # Note: Use enum.Enum, not Enum
    pending = "pending"
    approved = "approved"
    disapproved = "disapproved"
    flagged = "flagged"
    draft = "draft"
    
class PropertyImage(Base):
    __tablename__ = 'property_images'

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey('properties.id', ondelete='CASCADE'))
    image_url = Column(Text, nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

    property = relationship("Property", back_populates="images")

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, server_default=Identity())
    property_name = Column(String(255), unique=True, nullable=True)
    owner_name = Column(String(255))
    type = Column(String(100))
    price = Column(DECIMAL(12, 2))
    area_sq_m = Column(DECIMAL(10, 2))
    unit = Column(String(50))
    murabba = Column(Integer, nullable=True)
    khasra = Column(String(255), nullable=True)
    khewat = Column(String(250), nullable=True)
    khata = Column(String(250), nullable=True)
    owner_details_en = Column(Text, nullable=True)
    owner_details_hi = Column(Text, nullable=True)
    state = Column(String(100))
    district = Column(String(100))
    tehsil = Column(String(100), nullable=True)
    village = Column(String(100))
    landmark = Column(String(255), nullable=True)
    verified = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    centroid = Column(Geography(geometry_type='POINT', srid=4326))
    geom = Column(JSONB, nullable=False)
    visits = Column(Integer, default=0)
    listed_date = Column(Date, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    status = Column(Enum(PropertyStatus), default=PropertyStatus.pending)
    flag_reason = Column(Text, nullable=True)
    user_uploaded = Column(Boolean, default=False)
    phone = Column(String(20))
    email = Column(String(255))

    images = relationship("PropertyImage", back_populates="property")
    # favorited_by = relationship("FavoriteProperty", back_populates="property")

