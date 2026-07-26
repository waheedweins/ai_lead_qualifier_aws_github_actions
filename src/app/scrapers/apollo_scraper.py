import logging
import requests
from src.app.core.settings import settings
from src.app.utils.retry import retry

logger = logging.getLogger("lead-engine.scrapers.apollo")


class ApolloScraper:
    """
    Uses Apollo.io API to:
    1. Search people by company name / domain to find decision-maker emails
    2. Enrich existing leads with verified contact info
    """

    def __init__(self):
        self.api_key = settings.APOLLO_API_KEY
        # Fallback to official v1 base URL if not explicitly defined in settings
        self.base_url = getattr(settings, "APOLLO_BASE_URL", "https://api.apollo.io/v1")
        self.enabled = bool(self.api_key)
        if not self.enabled:
            logger.info("Apollo: APOLLO_API_KEY not set — Apollo enrichment disabled.")

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

    def search_people(
        self,
        company_name: str,
        titles: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search Apollo for decision-makers at a company.
        """
        if not self.enabled:
            return []

        titles = titles or ["owner", "CEO", "founder", "director", "manager"]
        payload = {
            "q_organization_name": company_name,
            "person_titles": titles,
            "page": 1,
            "per_page": limit,
            "contact_email_status": ["verified", "guessed"],
        }

        def _call():
            r = requests.post(
                f"{self.base_url}/mixed_people/search",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return r.json()

        try:
            data = retry(_call, retries=2, delay=2.0)
            people = data.get("people", [])
            results = []
            for p in people:
                email = p.get("email") or ""
                if not email or any(x in email for x in ["@example", "@test", "null"]):
                    continue
                results.append({
                    "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                    "email": email,
                    "phone": p.get("phone_numbers", [{}])[0].get("raw_number") if p.get("phone_numbers") else None,
                    "title": p.get("title", ""),
                    "company": p.get("organization_name", company_name),
                    "linkedin": p.get("linkedin_url", ""),
                    "source": "apollo",
                })
            logger.info(f"Apollo found {len(results)} contacts for '{company_name}'")
            return results
        except Exception as e:
            logger.error(f"Apollo people search failed for '{company_name}': {e}")
            return []

    def enrich_lead(self, email: str) -> dict:
        """
        Enrich a known email address with Apollo data.
        """
        if not self.enabled or not email:
            return {}

        def _call():
            r = requests.post(
                f"{self.base_url}/people/match",
                headers=self._headers(),
                json={"email": email, "reveal_personal_emails": False},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()

        try:
            data = retry(_call, retries=2, delay=2.0)
            person = data.get("person", {})
            if not person:
                return {}
            return {
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "phone": person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
                "linkedin": person.get("linkedin_url", ""),
                "company": person.get("organization_name", ""),
                "website": person.get("organization", {}).get("website_url", ""),
            }
        except Exception as e:
            logger.error(f"Apollo enrichment failed for '{email}': {e}")
            return {}

    def search_companies(self, industry: str, location: str, limit: int = 20) -> list[dict]:
        """
        Search Apollo for companies in an industry+location.
        """
        if not self.enabled:
            return []

        payload = {
            "q_organization_keyword_tags": [industry],
            "organization_locations": [location],
            "page": 1,
            "per_page": limit,
        }

        def _call():
            r = requests.post(
                f"{self.base_url}/mixed_companies/search",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return r.json()

        try:
            data = retry(_call, retries=2, delay=2.0)
            companies = data.get("organizations", [])
            results = []
            for c in companies:
                results.append({
                    "name": c.get("name", ""),
                    "email": c.get("contact_email") or f"info@{c.get('primary_domain', 'unknown.com')}",
                    "phone": c.get("sanitized_phone", ""),
                    "address": c.get("raw_address", ""),
                    "website": c.get("website_url", ""),
                    "title": c.get("industry", industry),
                    "source": "apollo_company",
                })
            logger.info(f"Apollo company search: {len(results)} results for '{industry}' in '{location}'")
            return results
        except Exception as e:
            logger.error(f"Apollo company search failed: {e}")
            return []
