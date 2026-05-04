# 🎫 Ticket System

> ML-powered support ticket management — FastAPI · PostgreSQL · Redis · Celery · Nginx · Docker

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

Clients submit support tickets and an **XGBoost ML model** automatically predicts priority (Low / Medium / High / Critical) via an async Celery worker. Workers can view all tickets, see predictions, and update statuses. The full stack runs in Docker with Nginx load balancing across 3 FastAPI instances.

---

## Features

- 🤖 **Auto priority prediction** — XGBoost + TF-IDF classifies tickets in the background
- ⚡ **Async processing** — Celery handles ML inference and email notifications non-blocking
- 🔁 **Load balanced** — Nginx round-robins across 3 FastAPI instances
- 🔐 **JWT auth** — Stateless authentication with Redis-backed token revocation
- 👥 **Role-based access** — Clients see their own tickets; workers see all
- 📧 **Email notifications** — Clients notified when prediction completes

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Python |
| Database | PostgreSQL 15 |
| Cache / Broker | Redis 7 |
| Task Queue | Celery |
| ML Model | XGBoost + TF-IDF (scikit-learn) |
| Load Balancer | Nginx |
| Containers | Docker + Docker Compose (7 services) |
| Frontend | Vanilla JS / HTML (single file, no build step) |

---

## Getting Started

**Prerequisites:** Docker Desktop, Git, trained `.pkl` model in `model_training/model/`

```bash
git clone https://github.com/your-username/ticket-system.git
cd ticket-system

cp .env.example .env
# Edit .env — set AUTH_SECRET_KEY, MODEL_PATH, and EMAIL_* credentials

docker compose up --build
```

Open `http://localhost` — API docs at `http://localhost/docs`.

---

## Project Structure

```
ticket_system/
├── app/                  # FastAPI app (routes, models, auth, tasks)
├── model_training/       # Jupyter notebook + training data + saved .pkl
├── nginx/                # Load balancer config
├── docker-compose.yml    # 7 services: db, redis, app1-3, celery, nginx
├── Dockerfile
└── ticket_system_v3_beautiful.html  # Frontend SPA
```

---

## How It Works

1. Client submits a ticket → saved to PostgreSQL with `status = open`
2. Celery task queued in Redis immediately (API returns instantly)
3. Worker runs XGBoost inference → saves priority + confidence to DB
4. Redis cache invalidated → client email sent

---

## Environment Variables

| Variable | Description |
|---|---|
| `AUTH_SECRET_KEY` | JWT signing secret |
| `MODEL_PATH` | Path to `.pkl` model inside container |
| `DATABASE_URL_DOCKER` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `EMAIL_HOST / PORT / USER / PASS` | SMTP credentials |

---

Built by **Manish** · v1.0.0 · May 2026
