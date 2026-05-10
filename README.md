# 🏠 County Real Estate Platform

A full-stack WeChat Mini Program for county-level real estate information, built with **WeChat Mini Program** + **Python FastAPI** + **MySQL**.

> Live at `https://api.imlemon.top` · Mini Program ID: `wx6a6c44c768f90ba9`

---

## ✨ Features

### For Home Buyers
- 🏘️ **Property Search** — Filter by price, area, type, location, and keywords
- 📍 **Map View** — Browse properties on an interactive map with location-based search
- ⚖️ **Property Compare** — Compare up to 4 properties side-by-side
- 🔔 **Price Alerts** — Track favorited properties and get notified on price drops
- 🧮 **Mortgage Calculator** — Local calculation with equal installment/principal methods
- 🏘️ **Community View** — See all listings in the same community with price stats
- 🖼️ **Share Poster** — Generate property posters via Canvas 2D for social sharing
- 📞 **One-Tap Call** — Direct phone call to property agents

### For Agents
- 📊 **Agent Dashboard** — Workbench with stats (property, appointment, customer)
- 🏠 **Property Management** — CRUD operations for listings with image upload
- 👥 **Customer Management** — Track customers and their preferences

### Tech Highlights
- 🎨 **Design System** — CSS custom properties with consistent spacing/color/shadow tokens
- ⚡ **Skeleton Loading** — Skeleton screens with staggered fade-in animations
- 🔒 **JWT Auth** — Secure authentication with WeChat OAuth + rate limiting
- 📱 **Lazy Loading** — `lazyCodeLoading: requiredComponents` for performance

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | WeChat Mini Program (Native) |
| **Backend** | Python 3.12 + FastAPI |
| **Database** | MySQL 8.0 + SQLAlchemy (async) |
| **Cache** | Redis |
| **Auth** | JWT + bcrypt + WeChat OAuth |
| **Server** | Alibaba Cloud ECS (2C2G) + Nginx + Let's Encrypt SSL |

---

## 📁 Project Structure

```
county-real-estate-platform/
├── miniprogram/           # WeChat Mini Program
│   ├── pages/
│   │   ├── index/         # Home (hero + search + hot properties)
│   │   ├── property/      # Property pages
│   │   │   ├── list/      # Property list with filters
│   │   │   ├── detail/    # Property detail (images, info, agent)
│   │   │   ├── compare/   # Property comparison
│   │   │   ├── community/ # Community-level view
│   │   │   ├── poster/    # Canvas poster generator
│   │   │   ├── search/    # Search page
│   │   │   ├── map/       # Map view
│   │   │   └── add/       # Add property (agents)
│   │   ├── agent/         # Agent workbench & management
│   │   ├── user/          # Profile, favorites, appointments
│   │   ├── login/         # Login & registration
│   │   ├── tools/         # Mortgage calculator
│   │   └── news/          # Real estate news
│   ├── utils/             # Utilities (API, format, compare, cache)
│   ├── app.js / app.json / app.wxss
│   └── project.config.json
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/        # REST API endpoints
│   │   ├── core/          # Config, security, database, rate_limit
│   │   ├── crud/          # Database CRUD operations
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic validation schemas
│   │   └── utils/         # Upload, WeChat, validators
│   ├── requirements.txt
│   └── run.py
├── deploy/                # Deployment configs
│   ├── nginx.conf         # HTTPS + reverse proxy
│   ├── production.env     # Environment template
│   ├── deploy.sh          # One-click deploy script
│   └── supervisor.conf    # Process manager config
└── sql/                   # Database schema
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- MySQL 8.0+
- Redis (optional, for caching)
- WeChat Mini Program AppID

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp ../deploy/production.env .env
# Edit .env with your DB credentials, WeChat AppID/Secret

# Initialize database
python3 -c "
import asyncio
from app.core.database import engine, Base
from app.models import *
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
"

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Mini Program Setup

1. Open `miniprogram/` in WeChat DevTools
2. Update `app.js` → `baseUrl` to your API address
3. Compile and test

---

## 🔒 Security

- ✅ JWT with bcrypt password hashing
- ✅ Rate limiting on auth endpoints (10 req/60s)
- ✅ CORS whitelist (methods + origins)
- ✅ `.env` excluded from git via `.gitignore`
- ✅ No hardcoded credentials or dev backdoors
- ✅ Soft-delete pattern for data safety

---

## 📊 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Health check |
| `POST` | `/api/v1/auth/login` | No | Phone login |
| `POST` | `/api/v1/auth/wechat/login` | No | WeChat login |
| `GET` | `/api/v1/properties` | No | List/search properties |
| `GET` | `/api/v1/properties/{id}` | No | Property detail |
| `POST` | `/api/v1/properties` | Yes | Create property |
| `GET` | `/api/v1/favorites/` | Yes | User favorites |
| `GET` | `/api/v1/news/` | No | Real estate news |
| `GET` | `/api/v1/agents/workbench` | Yes | Agent dashboard |

---

## 🔧 Deployment

See `deploy/DEPLOYMENT_GUIDE.md` for full Alibaba Cloud deployment instructions including Nginx HTTPS setup, Supervisor process management, and WeChat backend configuration.

---

## 📝 License

MIT © [LemonGan](https://github.com/LemonGan)
