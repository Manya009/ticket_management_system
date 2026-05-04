from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
import os

from .models import TicketCategory, TicketStatus


#1. Define Login and Signup schemas for user authentication. These will be used to validate the data sent to the /auth/signup and /auth/login routes.
class LoginSchema(BaseModel):
    email: str
    password: str

class SignupSchema(BaseModel):
    email: str
    password: str
    is_client: Optional[bool] = False
    is_worker: Optional[bool] = False
    worker_id: Optional[int] = None  # Only for workers, can be null for clients

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword",
                "is_client": True,
                "is_worker": False,
                "worker_id": None
            }
        }

#2. Define schemas for tickets and predictions. These will be used to validate the data sent to the ticket management routes.
class TicketSchema(BaseModel):
    user_id: str
    ticket_id: int
    title: str
    description: Optional[str] = None
    
    # Just use the Enum directly! Pydantic handles everything else automatically.
    category: TicketCategory
    status: TicketStatus
    
    time_created: Optional[datetime] = None 

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "ticket_id": 123,
                "title": "Issue with product",
                "description": "Details...",
                "category": "technical",
                "status": "open"
            }
        }
    )

class PredictionSchema(BaseModel):
    ticket_id: int
    user_id: str
    title: str
    description: Optional[str] = None
    
    # Use the Enum here too
    category: TicketCategory
    
    priority: Optional[str] = None
    confidence: Optional[float] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "ticket_id": 123,
                "user_id": "user123",
                "title": "Issue with product",
                "category": "technical",
                "priority": "High",
                "confidence": 0.95
            }
        }
    )

class PredictionResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: str
    category: TicketCategory
    priority: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)

#3. Define settings for JWT authentication. This will load the secret key from the environment variable and use it to configure the JWT settings.
from dotenv import load_dotenv
load_dotenv()
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
class Settings(BaseModel):
    authjwt_secret_key: str = AUTH_SECRET_KEY
    authjwt_blacklist_enabled: bool = True
    authjwt_blacklist_token_checks: set = {"access", "refresh"}
