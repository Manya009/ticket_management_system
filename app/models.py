# app/models.py
import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from .database import Base

# 1. Define standard Python Enums
class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"

class TicketCategory(str, enum.Enum):
    technical = "technical"
    billing = "billing"
    cancellation = "cancellation"
    product = "product"
    refund = "refund"

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_client = Column(Boolean, default=False)
    is_worker = Column(Boolean, default=False)
    worker_id = Column(Integer, nullable=True)

class Ticket(Base):
    __tablename__ = "tickets"
    ticket_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String) 
    title = Column(String)
    description = Column(Text)
    
    # 2. Use SQLAlchemy's native Enum column
    category = Column(SQLEnum(TicketCategory))
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.open)
    
    time_created = Column(DateTime(timezone=True), server_default=func.now())

class Predictions(Base):
    __tablename__ = "predictions"
    # Ensure this has primary_key=True
    id = Column(Integer, primary_key=True, index=True) 
    ticket_id = Column(Integer)
    user_id = Column(String) 
    category = Column(SQLEnum(TicketCategory))
    priority = Column(String) 
    confidence = Column(Float)