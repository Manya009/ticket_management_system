from .celery_worker import celery
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ticket, Predictions, User
import joblib
import pandas as pd
from .redis_client import redis_client
import json
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_PATH = os.getenv("MODEL_PATH")


@celery.task
def process_ticket(ticket_id: int):

    db: Session = SessionLocal()

    try:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return

        # 🔥 LOAD MODEL (same as your /predict route)
        artifacts = joblib.load(MODEL_PATH)
        xgb_model = artifacts["xgb_model"]
        tfidf = artifacts["tfidf_vectorizer"]
        expected_columns = artifacts["expected_columns"]

        # 🔥 PREP DATA (IMPORTANT: includes category)
        row_df = pd.DataFrame([{
            "Ticket Type": ticket.category,
            "Ticket Subject": ticket.title,
            "Ticket Description": ticket.description or ""
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

        priority_map_inv = {
            0: "Low",
            1: "Medium",
            2: "High",
            3: "Critical"
        }

        # 🔥 SAVE RESULT
        pred = Predictions(
            ticket_id=ticket.ticket_id,
            user_id=ticket.user_id,
            category=ticket.category,
            priority=priority_map_inv[pred_class],
            confidence=float(pred_proba[pred_class])
        )

        db.add(pred)
        db.commit()

        redis_client.delete("all_tickets")
        redis_client.delete(f"user_tickets:{ticket.user_id}")

        user = db.query(User).filter(User.user_id == ticket.user_id).first()

        # 📧 (optional for now)
        print(f"EMAIL is here -> Ticket {ticket.ticket_id} | Priority: {priority_map_inv[pred_class]}")
        send_email_task.delay(user.email, 
                              ticket.ticket_id, 
                              priority_map_inv[pred_class], 
                              float(pred_proba[pred_class]))
        print(f"📧 Email task triggered for {user.email}")

    finally:
        db.close()


from .email_utils import send_email

@celery.task
def send_email_task(email: str, ticket_id: int, priority: str, confidence: float):
    subject = f"Ticket #{ticket_id} Analysis Result"

    body = f"""
            Hello User,

            Your ticket (ID: {ticket_id}) has been processed.

            Predicted Priority: {priority}
            Confidence: {round(confidence * 100, 2)}%

            Our team will get back to you soon.

            Regards,
            Support Team
            """

    send_email(email, subject, body)

    print(f"📧 Email sent to {email}")