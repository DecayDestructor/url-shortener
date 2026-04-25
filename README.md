# snip.ly — URL Shortener

snip.ly lets you turn any long URL into a short, trackable link. It is built with FastAPI, React, PostgreSQL, and Redis, and runs on AWS EC2 with an automated Jenkins CI/CD pipeline.


---

## Table of Contents

- [Features](#features)
- [How the App Works](#how-the-app-works)
- [Service Breakdown](#service-breakdown)
- [API Reference](#api-reference)
- [Setup Guide](#setup-guide)
- [Environment Variables](#environment-variables)

---

## Features

- **URL Shortening**: Any valid URL becomes a short Base62 link. If you shorten the same URL twice, the original short code is returned instead of creating a duplicate.
- **Custom Aliases**: Choose your own short code (3-30 characters, letters/digits/underscore/hyphen). Reserved words like `admin` and `docs` are not allowed.
- **Link Expiration**: Set how long a link should stay active (in hours). After it expires, it returns 410 Gone.
- **QR Codes**: Every link gets a QR code automatically. You can download it as a PNG.
- **Click Tracking**: Every visit records the device type, referrer, and browser. Counts are saved to Redis first and written to the database in the background.
- **Analytics**: See total clicks, device breakdown, top referrers, and the last 50 visits for any link you own.
- **Trending**: A public leaderboard shows the top 5 most-clicked links in real time.
- **Rate Limiting**: You can shorten at most 5 URLs per minute per IP. If Redis is down, the limit is skipped instead of blocking everyone.
- **JWT Authentication**: All write operations require you to be logged in. Tokens are signed and stateless.
- **Role-Based Access**: Regular users manage their own links. Admins can see and manage everything.
- **Link Deletion**: Deleting a link removes it from the database, cache, click counter, and trending list.

---

## How the App Works

```
Browser
   |
   v
React + Nginx (port 80)
   |-- /api/*  ----------> FastAPI (port 8000) --> PostgreSQL
   |-- /{short_code} ----> FastAPI (port 8000) --> Redis (cache/counters/trending)
   |-- /*      ----------> React index.html
```

### Shorten a URL

```
POST /shorten
   |
   v
Rate limit check (Redis counter per IP, max 5/min)
   |
   v
Custom alias? -> validate + check conflicts
Auto code?    -> increment Redis counter, Base62 encode
   |
   v
Save to PostgreSQL -> cache in Redis -> return short URL + QR code
```

### Redirect

```
GET /{short_code}
   |
   v
Redis cache hit? -> redirect immediately, increment click counter
   |
Redis miss -> query PostgreSQL -> check expiry
   |
Expired -> 410 Gone
Valid   -> cache in Redis, redirect, increment counter
   |
   v
Background: save ClickEvent, sync DB if count % 50 == 0
```

---

## Service Breakdown

### FastAPI Backend

The backend handles all business logic.

- **Auth**: Passwords are hashed with bcrypt. Login returns a JWT token that carries the user ID and admin flag.
- **Short codes**: A global counter in Redis is incremented for every new link and encoded into Base62 to produce the short code.
- **Caching**: The first time a short link is visited, the destination is stored in Redis. Future visits are served from cache without touching the database.
- **Click sync**: Click counts go to Redis first (fast). A background job syncs them to PostgreSQL every 5 minutes. Each click also writes a full event record asynchronously.

### React Frontend

A single-page app built with React and Vite. It talks to the backend through Nginx at `/api/*`.

- Home page: URL input, live trending leaderboard, feature overview
- Dashboard: your own links with click counts and delete option
- Admin portal: all links from all users, sortable by clicks
- Auth pages: register and login; the token is saved in localStorage and sent with every request

### Nginx

Nginx sits inside the frontend container and routes traffic:

- `/api/*` goes to the FastAPI backend
- `/{short_code}` also goes to FastAPI to handle the redirect
- Everything else serves the React app
- JS, CSS, and image files are cached for 1 year

### PostgreSQL

Stores all persistent data across three tables: `user` (accounts), `url` (short links with owner, expiry, click count), and `clickevent` (one row per click, with device, referrer, and timestamp). Hosted on Neon (serverless PostgreSQL).

### Redis

Four key uses:

| Key pattern | Purpose |
|-------------|---------|
| `url:{short_code}` | URL cache for fast redirects |
| `clicks:{short_code}` | Click counter, synced to DB periodically |
| `trending_urls` | Sorted set tracking clicks per code |
| `rate_limit:{ip}` | Per-IP request counter with 60s TTL |

### Jenkins CI/CD Pipeline

Every build runs five stages automatically:

1. **Checkout**: gets the latest code from GitHub
2. **Install Dependencies**: installs Python packages from requirements.txt
3. **Run Tests**: sets up a temporary SQLite environment and runs all 85 pytest tests
4. **Build and Push**: builds Docker images for both frontend and backend, then pushes them to Docker Hub
5. **Deploy**: connects to EC2 over SSH, pulls the new images, and restarts the containers

Two credentials need to be added in Jenkins:
- `dockerhub-creds`: your Docker Hub username and password
- `ec2-ssh-key`: the SSH private key for your EC2 server (username: `ubuntu`)

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | None | Create account |
| POST | /auth/login | None | Login, receive JWT |
| POST | /auth/admin/login | None | Admin login |
| GET | /auth/me | User | Current user info |
| POST | /shorten | User | Create short URL |
| GET | /{short_code} | None | Redirect to original |
| GET | /stats/{short_code} | None | Click count and metadata |
| GET | /analytics/{short_code} | Owner/Admin | Full analytics |
| GET | /urls/me | User | All links owned by user |
| DELETE | /urls/{short_code} | Owner/Admin | Delete a link |
| GET | /trending/public | None | Top 5 trending links |
| GET | /admin/urls | Admin | All links, all users |
| GET | /admin/trending | Admin | Trending with full detail |

---

## Setup Guide

### Prerequisites

- Git and Docker
- A PostgreSQL database URL (Neon free tier works: https://neon.tech)

### Run with Docker

This works the same on Ubuntu, macOS, and Windows.

**Ubuntu** — install Docker first if you do not have it:
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**macOS / Windows** — install Docker Desktop from https://www.docker.com/products/docker-desktop. On Windows, turn on WSL 2 integration in Docker Desktop settings.

Then run:

```bash
git clone https://github.com/VriVa/URL-shortener.git
cd URL-shortener
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY, etc.
docker compose up -d --build
curl -X POST http://localhost/api/auth/admin/seed
```

Open http://localhost in your browser. API docs at http://localhost:8000/docs.

Default admin: `admin@snip.ly` / `admin123` (change after first login).

### Local Development Without Docker

**Backend**:
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
.\venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**:
```bash
cd client
npm install
npm run dev                     # Runs on http://localhost:5173
```

Ensure Redis is running locally on port 6379 and `.env` is configured.

### Jenkins Setup

```bash
docker run -d --name jenkins -u root \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts

docker exec -it -u root jenkins bash
apt-get update && apt-get install -y docker.io python3 python3-pip
```

Add credentials in Jenkins UI, create a Pipeline job pointing to this repo, and set the branch to `main`.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection URL |
| `BASE_URL` | Public base URL for generated short links |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens |
