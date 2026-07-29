AI Lead Qualifier v2 🚀Production-grade AI-powered lead generation, enrichment, scoring, and outreach system. Designed from end to end for individuals or developers who cannot afford expensive paid APIs, offering a completely functional, production-ready stack deployed on AWS EC2 using GitHub Actions and GitHub Packages. Powered by Gemini 3.5 Flash for state-of-the-art AI reasoning and speed.Full PipelinePOST /scrape/run?query=solar+installers+lahore&source=all
        │
        ├─── Google Maps (Apify) ──┐
        │                         ├─→ Lead Ingestor → PostgreSQL
        └─── Apollo.io ────────────┘
                    │
                    ▼
            Apollo Enrichment
            (phone, website, title)
                    │
                    ▼
            Tavily Web Search
            (online presence summary)
                    │
                    ▼
            Gemini 3.5 Flash AI Scoring
            (0-100 score + reason)
                    │
               ┌────┴────┐
              HOT       COLD
             (≥50)      (<50)
               │
               ▼
        Gemini 3.5 Flash writes
        personalised message
               │
          ┌────┴─────┐
       WhatsApp     Email
      (if phone)  (SendGrid)
What's New in v2Featurev1v2AI scoringHeuristic rulesGemini 3.5 FlashWebsite enrichment✗Tavily searchApollo.io integration✗✓ people + company searchOutreach messagesTemplate stringGemini 3.5 Flash-personalisedWhatsApp fallback✗Falls back to emailPhone normalisation✗E.164 auto-formatPipeline endpoint✗POST /scrape/runStats endpoint✗GET /leads/statsRescore endpoint✗POST /leads/{id}/scorePlaceholder emailsIngestedFiltered outai_reason in DB✗✓ stored per lead⚙️ Configuration & Test Mode LimitsTo ensure smooth testing without hitting external API rate limits (such as Gemini Free Tier quotas or Apollo plan restrictions) and to streamline local development, the pipeline incorporates the following test-mode safeguards:Google Maps Scraper: Unrestricted to pull complete local business datasets for thorough testing.Apollo Scraper & Ingestion: Capped at a maximum of 2 records to align with safe usage policies.LLM Batch Processing (lead_processor): Automatically throttled to a maximum of 2 leads per batch run during local execution to prevent 429 rate-limit errors on free-tier LLM endpoints.Auth0 Integration: Temporarily bypassed and commented out on local/test lead routes to reduce architecture complexity.Deployment & CI/CD (AWS EC2 & GitHub Actions)Infrastructure: Hosted and deployed end-to-end on an AWS EC2 instance.CI/CD Pipeline: Fully automated deployment workflows managed via GitHub Actions.Container Registry: Built container images are securely stored and pulled using GitHub Packages (GHCR).Quick Start (Local)Bash# 1. Clone
git clone https://github.com/waheedweins/ai_lead_qualifier_aws_github_actions
cd ai_lead_qualifier_aws_github_actions

# 2. Set up env
cp .env.example .env
# Fill in your keys (Gemini is free, Tavily is free)

# 3. Run
docker-compose up --build

# 4. Test full pipeline
curl -X POST "http://localhost:8000/scrape/run?query=solar+installers+lahore&source=all"

# 5. Check leads
curl http://localhost:8000/leads/
curl http://localhost:8000/leads/stats
AWS Secrets ManagerAdd all keys to production/LeadQualifier:JSON{
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
API ReferenceMethodEndpointDescriptionGET/health/Health checkPOST/scrape/?query=...&source=google_mapsScrape onlyPOST/scrape/processScore + outreach all new leads (Test mode: max 2)POST/scrape/run?query=...&source=allFull pipelinePOST/leads/Add single lead manuallyGET/leads/List all leadsGET/leads/statsDashboard statsGET/leads/{id}Get lead by IDPOST/leads/{id}/scoreRe-score a leadFree API KeysServicePurposeLinkGemini 3.5 FlashAI scoring & message writinghttps://aistudio.google.com/app/apikeyTavilyWebsite enrichmenthttps://tavily.comApolloB2B contact enrichmenthttps://app.apollo.io/#/settings/integrations/apiApifyGoogle Maps scrapinghttps://apify.comSendGridEmail outreachhttps://sendgrid.com (100/day free)
