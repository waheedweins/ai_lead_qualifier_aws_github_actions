````markdown
# AI Lead Qualifier v2 🚀

A **production-grade AI-powered lead generation, enrichment, scoring, and outreach system**.

Built for **developers, freelancers, and small businesses** who cannot afford expensive AI APIs, this project provides a complete end-to-end lead generation pipeline using **Gemini 3.5 Flash**, **Apollo**, **Apify**, **Tavily**, **PostgreSQL**, **Docker**, **AWS EC2**, and **GitHub Actions**.

---

# ✨ Features

- 🤖 AI-powered lead scoring using **Gemini 3.5 Flash**
- 🗺️ Google Maps lead scraping via **Apify**
- 👥 Apollo company & people enrichment
- 🌐 Website enrichment using **Tavily Search**
- 💬 AI-generated personalised outreach messages
- 📧 Email outreach via SendGrid
- 📱 WhatsApp outreach (with automatic email fallback)
- 📊 Lead statistics dashboard
- 🔄 Re-score leads anytime
- 🐳 Dockerized
- ☁️ AWS EC2 Deployment
- 🔁 GitHub Actions CI/CD
- 📦 GitHub Container Registry (GHCR)

---

# 🏗️ System Architecture

```text
POST /scrape/run?query=solar+installers+lahore&source=all
        │
        ├── Google Maps (Apify)
        │
        └── Apollo Company Search
                     │
                     ▼
              Lead Ingestor
             (PostgreSQL Database)
                     │
                     ▼
            Apollo Enrichment
     (Phone, Website, Job Title, etc.)
                     │
                     ▼
             Tavily Web Search
      (Online Presence & Summary)
                     │
                     ▼
        Gemini 3.5 Flash AI Scoring
         (Score 0–100 + AI Reason)
                     │
              ┌──────┴──────┐
              │             │
            HOT           COLD
          (≥ 50)         (< 50)
              │
              ▼
 Gemini 3.5 Flash generates
 personalised outreach message
              │
        ┌─────┴────────┐
        │              │
   WhatsApp        SendGrid Email
 (if phone exists)   (fallback)
```

---

# 🚀 What's New in v2

| Feature | v1 | v2 |
|----------|:--:|:--:|
| AI Scoring | Heuristic Rules | ✅ Gemini 3.5 Flash |
| Website Enrichment | ❌ | ✅ Tavily Search |
| Apollo Integration | ❌ | ✅ Company + People Search |
| Outreach Messages | Static Template | ✅ AI Personalised |
| WhatsApp Fallback | ❌ | ✅ Email Fallback |
| Phone Normalisation | ❌ | ✅ E.164 Formatting |
| Full Pipeline Endpoint | ❌ | ✅ `/scrape/run` |
| Dashboard Statistics | ❌ | ✅ `/leads/stats` |
| Re-score Endpoint | ❌ | ✅ `/leads/{id}/score` |
| Placeholder Emails Filter | ❌ | ✅ Automatically Removed |
| AI Reason Stored | ❌ | ✅ Saved in Database |

---

# ⚙️ Test Mode (Rate-Limit Friendly)

To avoid exhausting free API quotas during development, the application automatically limits several services while running locally.

| Component | Behaviour |
|------------|-----------|
| Google Maps Scraper | No limits |
| Apollo Scraper | Maximum **2 leads** |
| Lead Processor | Maximum **2 leads per batch** |
| Gemini Processing | Limited to avoid HTTP 429 errors |
| Auth0 | Disabled for local testing |

These safeguards make the project fully usable on free API tiers.

---

# ☁️ Deployment

Production deployment uses:

- AWS EC2
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)

Deployment flow:

```text
Git Push
    │
    ▼
GitHub Actions
    │
Build Docker Image
    │
Push to GHCR
    │
SSH into EC2
    │
Pull Latest Image
    │
Restart Containers
```

---

# 🚀 Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/waheedweins/ai_lead_qualifier_aws_github_actions
cd ai_lead_qualifier_aws_github_actions
```

---

## 2. Configure Environment

```bash
cp .env.example .env
```

Fill in your API keys.

Gemini and Tavily both provide generous free tiers for development.

---

## 3. Run the Project

```bash
docker-compose up --build
```

---

## 4. Run Full Pipeline

```bash
curl -X POST \
"http://localhost:8000/scrape/run?query=solar+installers+lahore&source=all"
```

---

## 5. View Leads

```bash
curl http://localhost:8000/leads/
```

---

## 6. Dashboard Statistics

```bash
curl http://localhost:8000/leads/stats
```

---

# 🔐 AWS Secrets Manager

Store all production secrets inside:

```
production/LeadQualifier
```

Example:

```json
{
  "DATABASE_URL": "postgresql://...",
  "APIFY_API_TOKEN": "apify_api_...",
  "APOLLO_API_KEY": "your_apollo_key",
  "GEMINI_API_KEY": "AIzaSy...",
  "TAVILY_API_KEY": "tvly-...",
  "SENDGRID_API_KEY": "SG...",
  "EMAIL_FROM": "outreach@yourdomain.com",
  "WHATSAPP_TOKEN": "EAAxx...",
  "WHATSAPP_PHONE_ID": "123456789"
}
```

---

# 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health Check |
| POST | `/scrape?query=...&source=google_maps` | Scrape Only |
| POST | `/scrape/process` | Score & Process New Leads *(Test Mode: max 2 leads)* |
| POST | `/scrape/run?query=...&source=all` | Complete Pipeline |
| POST | `/leads` | Add Single Lead |
| GET | `/leads` | List All Leads |
| GET | `/leads/stats` | Dashboard Statistics |
| GET | `/leads/{id}` | Get Lead by ID |
| POST | `/leads/{id}/score` | Re-score Lead |

---

# 🔑 Free API Keys

| Service | Purpose | Link |
|----------|---------|------|
| Gemini 3.5 Flash | AI Lead Scoring & Outreach | https://aistudio.google.com/app/apikey |
| Tavily | Website Enrichment | https://tavily.com |
| Apollo | Company & Contact Enrichment | https://app.apollo.io/#/settings/integrations/api |
| Apify | Google Maps Scraping | https://apify.com |
| SendGrid | Email Outreach (100/day free) | https://sendgrid.com |

---

# 🛠️ Tech Stack

### Backend

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic

### AI

- Gemini 3.5 Flash
- Tavily Search

### Lead Sources

- Apify
- Apollo.io

### Outreach

- SendGrid
- WhatsApp Cloud API

### DevOps

- Docker
- Docker Compose
- GitHub Actions
- GitHub Packages (GHCR)
- AWS EC2

---

# 📊 Pipeline Summary

```text
Google Maps
      │
      ▼
Apollo Search
      │
      ▼
PostgreSQL
      │
      ▼
Apollo Enrichment
      │
      ▼
Tavily Search
      │
      ▼
Gemini AI Scoring
      │
      ▼
AI Personalised Outreach
      │
      ▼
WhatsApp / Email
```

---

# 📄 License

This project is intended for educational and production use.

Please ensure compliance with the terms of service of all third-party providers (Google, Apollo, Apify, Tavily, SendGrid, and Meta WhatsApp Cloud API).

---

## ⭐ If you found this project useful, consider giving it a star on GitHub!
````
