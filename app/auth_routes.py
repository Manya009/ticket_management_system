from fastapi import APIRouter, HTTPException, Depends, Request, Header
from .database import get_db
from .schemas import LoginSchema, SignupSchema
from .models import User
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from .redis_client import redis_client
from app.auth_utils import create_access_token, verify_token
import hashlib

auth_router = APIRouter(prefix="/auth", tags=["auth"])


async def generate_user_id(email: str) -> str:
    return hashlib.sha256(email.lower().encode()).hexdigest()[:16]


@auth_router.post("/signup")
async def signup(user: SignupSchema, db: Session = Depends(get_db)):
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.is_worker and not user.worker_id:
        raise HTTPException(status_code=400, detail="Worker ID is required")

    user_id = await generate_user_id(user.email)

    new_user = User(
        user_id=user_id,
        email=user.email,
        password=generate_password_hash(user.password),
        is_client=user.is_client,
        is_worker=user.is_worker,
        worker_id=user.worker_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@auth_router.post("/login")
async def login(user: LoginSchema, request: Request, db: Session = Depends(get_db)):

    ip = request.client.host
    key = f"login_attempts:{ip}"

    attempts = redis_client.incr(key)

    if attempts == 1:
        redis_client.expire(key, 60)

    if attempts > 5:
        raise HTTPException(status_code=429, detail="Too many attempts")

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email")

    if not check_password_hash(db_user.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    redis_client.delete(key)

    access_token = create_access_token({"sub": db_user.user_id})

    return {"access_token": access_token}


@auth_router.post("/logout")
async def logout(authorization: str = Header(...)):
    token = authorization.split(" ")[1]

    redis_client.setex(token, 3600, "revoked")

    return {"message": "Logged out"}