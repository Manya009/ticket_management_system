from fastapi import APIRouter, HTTPException, Depends, Header
from .database import get_db
from .schemas import TicketSchema, PredictionSchema, PredictionResponse
from .models import User, Ticket, Predictions, TicketStatus
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from .redis_client import redis_client
from .auth_utils import verify_token
import json
import os
from dotenv import load_dotenv
from .tasks import process_ticket

load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH")

ticket_router = APIRouter(prefix="/tickets", tags=["tickets"])


# 🔐 Auth helper
def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1]

    if redis_client.get(token):
        raise HTTPException(status_code=401, detail="Token revoked")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return payload["sub"]


# 🎫 CREATE TICKET
@ticket_router.post("/create", response_model=TicketSchema)
async def create_ticket(
    ticket: TicketSchema,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user(authorization)

    new_ticket = Ticket(
        user_id=user_id,
        title=ticket.title,
        description=ticket.description,
        category=ticket.category,
        status=TicketStatus.open
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    print("🔥 Triggering celery task...")
    
    # 🔥 CALL CELERY (ASYNC)
    process_ticket.delay(new_ticket.ticket_id)

    # clear cache
    redis_client.delete(f"user_tickets:{user_id}")
    redis_client.delete("all_tickets")

    return new_ticket


# 🤖 PREDICT PRIORITY
@ticket_router.post("/predict", response_model=PredictionResponse)
async def predict_ticket_category(
    prediction_request: PredictionSchema,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user(authorization)

    artifacts = joblib.load(MODEL_PATH)
    xgb_model = artifacts["xgb_model"]
    tfidf = artifacts["tfidf_vectorizer"]
    expected_columns = artifacts["expected_columns"]

    row_df = pd.DataFrame([{
        "Ticket Type": prediction_request.category,
        "Ticket Subject": prediction_request.title,
        "Ticket Description": prediction_request.description or ""
    }])

    row_encoded = pd.get_dummies(row_df[['Ticket Type', 'Ticket Subject']])
    text_matrix = tfidf.transform(row_df['Ticket Description'])

    row_text = pd.DataFrame(
        text_matrix.toarray(),
        columns=[f"word_{w}" for w in tfidf.get_feature_names_out()]
    )

    row_final = pd.concat([row_encoded, row_text], axis=1)\
        .reindex(columns=expected_columns, fill_value=0)

    pred_class = xgb_model.predict(row_final)[0]
    pred_proba = xgb_model.predict_proba(row_final)[0]

    priority_map_inv = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}

    new_prediction = Predictions(
        ticket_id=prediction_request.ticket_id,
        user_id=user_id,
        category=prediction_request.category,
        priority=priority_map_inv[pred_class],
        confidence=float(pred_proba[pred_class])
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    return new_prediction


# 👤 USER TICKETS
@ticket_router.get("/my_tickets")
async def get_my_tickets(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user(authorization)

    cache_key = f"user_tickets:{user_id}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    user_tickets = db.query(Ticket)\
        .filter(Ticket.user_id == user_id).all()

    result = []
    for ticket in user_tickets:
        pred = db.query(Predictions)\
            .filter(Predictions.ticket_id == ticket.ticket_id)\
            .first()

        result.append({
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "status": ticket.status,
            "category": ticket.category,
            "predicted_priority": pred.priority if pred else None,
            "confidence": pred.confidence if pred else None
        })

    redis_client.setex(cache_key, 600, json.dumps(result))
    return result


# 🛠 ADMIN / WORKER: ALL TICKETS
@ticket_router.get("/all_tickets")
async def get_all_tickets(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    user_id = get_current_user(authorization)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_worker:
        raise HTTPException(status_code=403, detail="Not authorized")

    cache_key = "all_tickets"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    tickets = db.query(Ticket).all()

    result = []
    for ticket in tickets:
        pred = db.query(Predictions)\
            .filter(Predictions.ticket_id == ticket.ticket_id)\
            .first()

        result.append({
            "ticket_id": ticket.ticket_id,
            "title": ticket.title,
            "status": ticket.status,
            "category": ticket.category,
            "predicted_priority": pred.priority if pred else None,
            "confidence": pred.confidence if pred else None
        })

    redis_client.setex(cache_key, 600, json.dumps(result))
    return result


# 🔄 UPDATE STATUS (WORKER ONLY)
@ticket_router.put("/update_status/{ticket_id}")
async def update_ticket_status(
    ticket_id: int,
    status: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db) ):

    user_id = get_current_user(authorization)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_worker:
        raise HTTPException(status_code=403, detail="Not authorized")

    ticket = db.query(Ticket)\
        .filter(Ticket.ticket_id == ticket_id)\
        .first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = TicketStatus(status)

    db.commit()
    db.refresh(ticket)

    # clear cache
    redis_client.delete("all_tickets")
    redis_client.delete(f"user_tickets:{ticket.user_id}")

    return {
        "message": "Ticket status updated",
        "ticket": ticket
    }