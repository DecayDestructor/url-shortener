# URL Shortener with Caching, Analytics & Trending URLs

 Hello! I built this small URL shortener project using FastAPI, Redis, and PostgreSQL (Neon), with a minimal Streamlit frontend.
It focuses on basic system design, scalability, caching strategies, and real-time analytics.

---

## Features

- Shorten long URLs using **Base62 encoding** for collision-safe short code generation
- Fast redirection using **Redis caching**
- Persistent storage using **PostgreSQL (Neon)**
- Click tracking using **Redis counters**
- Periodic sync of click data from Redis to database
- **Rate limiting** on URL creation to prevent abuse
- Cache expiration to keep analytics fresh
- View **Trending URLs** based on recent activity
- View all shortened URLs (admin)
- View real-time click counts (admin)

## Tech Stack used

#### Backend
- **FastAPI** – API framework
- **SQLModel** – ORM
- **PostgreSQL (Neon)** – Database
- **Redis** – Caching, counters, trending analytics
- **BackgroundTasks** – Async DB syncing

#### Frontend
- **Streamlit** – Minimal UI
---

## System Flow 

### URL Shortening Flow
When a user submits a long URL, the backend first checks whether the URL already exists in the database to avoid duplicates.If it does not exist, a **Base62 short code** is generated. The system ensures the short code is unique by checking for collisions in the database.
Once validated, the URL mapping is stored in PostgreSQL and a shortened URL is returned to the user. Rate limiting is applied at this step to prevent excessive URL creation requests.

---

### URL Redirection Flow
When a user accesses a shortened URL:
1. The backend first checks Redis to see if the original URL is cached.
2. If the URL is found in Redis, the user is immediately redirected (fast path).
3. If the URL is not cached, it is fetched from the database and then stored in Redis for future requests.
Each redirect increments a Redis-based click counter and updates the trending URLs data structure.

---

### Click Tracking & Syncing
Click counts are stored temporarily in Redis to avoid writing to the database on every request.
A background task periodically syncs these click counts from Redis into PostgreSQL, ensuring:
- High performance
- Accurate long-term analytics
- Reduced database load
After syncing, Redis counters are reset automatically using expiration.

---

### Trending URLs Logic
Trending URLs are tracked using a Redis **Sorted Set**, where:
- Each short code is a member
- Click count acts as the score
This allows efficient retrieval of the most accessed URLs within a recent time window.

---

### Statistics Retrieval Flow
When statistics for a short URL are requested:
- The backend fetches the persistent click count from PostgreSQL
- Any pending Redis clicks are merged
- The combined total is returned to the client
This guarantees accurate and up-to-date analytics.

---

### Admin Dashboard Flow
Admin endpoints aggregate data from both PostgreSQL and Redis to provide:
- All URLs with real-time click counts
- Top trending URLs
This ensures admins always see the latest system state.

---

## Setup Guide

### 1️. Clone the Repository
```bash
git clone https://github.com/your-username/url-shortener.git
cd url-shortener
```
### Backend Setup:
### 2. Install Dependencies
```bash
cd app
python -m venv venv
venv\Scripts\activate
or
source venv/bin/activate
pip install -r requirements.txt
```
### 3. Environment Variables
```bash
DATABASE_URL=postgresql+psycopg2://<username>:<password>@<neon-host>/<db-name>
REDIS_URL=redis://localhost:6379
BASE_URL=http://localhost:8000
```
### 4. Start Servers
```bash
redis-server
uvicorn app.main:app --reload
```
### VERIFY
```bash
http://localhost:8000
and
http://localhost:8000/docs
```
### Frontend Setup
```bash
cd frontend
streamlit run app.py
```
### VERIFY
```bash
http://localhost:8501
```

#### Hope you like this project, do reach out for feedback!
