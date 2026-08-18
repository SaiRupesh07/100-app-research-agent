"""
Official source discovery and retrieval layer.

This module discovers and retrieves official documentation pages for
the 100-app research pipeline.

Workflow:

    app name
        ↓
    known official domain
        ↓
    fetch official page
        ↓
    discover relevant same-domain links
        ↓
    fetch selected documentation pages
        ↓
    extract evidence
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from src.config import (
    MAX_RETRIES,
    MAX_SOURCES_PER_APP,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)

from src.research.evidence import (
    classify_source_type,
    validate_url,
)


logger = logging.getLogger(__name__)


# ============================================================
# KNOWN OFFICIAL DOCUMENTATION DOMAINS
# ============================================================

KNOWN_OFFICIAL_DOMAINS: Dict[str, str] = {
    "Salesforce": "https://developer.salesforce.com",
    "HubSpot": "https://developers.hubspot.com",
    "Pipedrive": "https://developers.pipedrive.com",
    "Attio": "https://developers.attio.com",
    "Twenty": "https://docs.twenty.com",
    "Podio": "https://developers.podio.com",
    "Zoho CRM": "https://www.zoho.com/crm/developer/",
    "Close": "https://developer.close.com",
    "Copper": "https://developer.copper.com",
    "Zendesk": "https://developer.zendesk.com",
    "Intercom": "https://developers.intercom.com",
    "Freshdesk": "https://developers.freshdesk.com",
    "Front": "https://dev.frontapp.com",
    "LiveAgent": "https://www.liveagent.com/api/",
    "Plain": "https://www.plain.com/docs",
    "Help Scout": "https://developer.helpscout.com",
    "Gorgias": "https://developers.gorgias.com",
    "Slack": "https://api.slack.com",
    "Twilio": "https://www.twilio.com/docs",
    "Zoho Cliq": "https://www.zoho.com/cliq/help/restapi/",
    "Lark": "https://open.larksuite.com/document/",
    "Discord": "https://discord.com/developers/docs",
    "Telegram": "https://core.telegram.org/bots/api",
    "WhatsApp Business": "https://developers.facebook.com/docs/whatsapp/",
    "Aircall": "https://developer.aircall.io",
    "Vonage": "https://developer.vonage.com",
    "Google Ads": "https://developers.google.com/google-ads/api",
    "Meta Ads": "https://developers.facebook.com/docs/marketing-apis/",
    "LinkedIn Ads": "https://learn.microsoft.com/linkedin/marketing/",
    "Mailchimp": "https://mailchimp.com/developer/",
    "Klaviyo": "https://developers.klaviyo.com",
    "Pinterest": "https://developers.pinterest.com",
    "Threads": "https://developers.facebook.com/docs/threads/",
    "SendGrid": "https://www.twilio.com/docs/sendgrid",
    "Shopify": "https://shopify.dev/docs",
    "WooCommerce": "https://developer.woocommerce.com",
    "BigCommerce": "https://developer.bigcommerce.com",
    "Magento / Adobe Commerce": "https://developer.adobe.com/commerce/",
    "Squarespace": "https://developers.squarespace.com",
    "Ecwid": "https://api-docs.ecwid.com",
    "Gumroad": "https://gumroad.com/api",
    "Apify": "https://docs.apify.com",
    "Firecrawl": "https://docs.firecrawl.dev",
    "Bright Data": "https://docs.brightdata.com",
    "GitHub": "https://docs.github.com/en/rest",
    "Vercel": "https://vercel.com/docs/rest-api",
    "Netlify": "https://docs.netlify.com/api/get-started/",
    "Cloudflare": "https://developers.cloudflare.com/api/",
    "Supabase": "https://supabase.com/docs",
    "Neo4j": "https://neo4j.com/docs/",
    "Snowflake": "https://docs.snowflake.com",
    "MongoDB Atlas": "https://www.mongodb.com/docs/atlas/api/",
    "Datadog": "https://docs.datadoghq.com/api/",
    "Sentry": "https://docs.sentry.io/api/",
    "Notion": "https://developers.notion.com",
    "Airtable": "https://airtable.com/developers/web/api",
    "Linear": "https://linear.app/developers",
    "Jira": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/",
    "Asana": "https://developers.asana.com",
    "Monday.com": "https://developer.monday.com/api-reference/",
    "ClickUp": "https://developer.clickup.com",
    "Coda": "https://coda.io/developers/apis/v1",
    "Smartsheet": "https://smartsheet.redoc.ly",
    "Harvest": "https://help.getharvest.com/api-v2/",
    "Stripe": "https://docs.stripe.com/api",
    "Plaid": "https://plaid.com/docs/api/",
    "Binance": "https://developers.binance.com",
    "QuickBooks": "https://developer.intuit.com",
    "Xero": "https://developer.xero.com",
    "NotebookLM": "https://support.google.com/notebooklm/",
    "Mermaid CLI": "https://mermaid.js.org",
}


# ============================================================
# DISCOVERY SETTINGS
# ============================================================

MAX_DISCOVERED_LINKS = 12

MAX_FETCHED_PAGES = 5

RELEVANCE_KEYWORDS = {
    "api": 5,
    "developer": 4,
    "authentication": 5,
    "auth": 4,
    "oauth": 5,
    "authorization": 4,
    "access-token": 4,
    "access_token": 4,
    "pricing": 3,
    "plans": 2,
    "mcp": 5,
    "model-context-protocol": 5,
    "webhook": 3,
    "rest": 3,
    "graphql": 3,
    "sdk": 2,
}


# ============================================================
# URL HELPERS
# ============================================================

def normalize_url(url: str) -> str:
    """Normalize a URL."""

    if not url:
        return ""

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return ""

    parsed = urlparse(url)

    # Remove fragments.
    normalized = parsed._replace(fragment="").geturl()

    return normalized.rstrip("/")


def same_domain(url_a: str, url_b: str) -> bool:
    """Check whether two URLs share the same hostname."""

    try:
        host_a = urlparse(url_a).netloc.lower()
        host_b = urlparse(url_b).netloc.lower()

        if host_a.startswith("www."):
            host_a = host_a[4:]

        if host_b.startswith("www."):
            host_b = host_b[4:]

        return host_a == host_b

    except Exception:
        return False


# ============================================================
# OFFICIAL DOMAIN
# ============================================================

def get_official_base_url(
    app_name: str,
) -> Optional[str]:
    """Return the known official documentation URL."""

    return KNOWN_OFFICIAL_DOMAINS.get(app_name)


# ============================================================
# LINK RELEVANCE
# ============================================================

def link_relevance(url: str) -> int:
    """
    Score a discovered URL based on useful research keywords.
    """

    parsed = urlparse(url)

    haystack = (
        f"{parsed.path} {parsed.query}"
    ).lower()

    score = 0

    for keyword, weight in RELEVANCE_KEYWORDS.items():

        if keyword in haystack:
            score += weight

    return score


def discover_links(
    base_url: str,
    html: str,
) -> List[str]:
    """
    Extract relevant same-domain links from an official page.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    candidates: List[tuple[int, str]] = []

    seen = set()

    for anchor in soup.find_all("a", href=True):

        href = anchor.get("href")

        if not href:
            continue

        absolute = normalize_url(
            urljoin(base_url, href)
        )

        if not absolute:
            continue

        if not same_domain(
            base_url,
            absolute,
        ):
            continue

        if absolute in seen:
            continue

        seen.add(absolute)

        score = link_relevance(
            absolute
        )

        if score <= 0:
            continue

        candidates.append(
            (
                score,
                absolute,
            )
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    return [
        url
        for _, url in candidates[:MAX_DISCOVERED_LINKS]
    ]


# ============================================================
# HTTP FETCH
# ============================================================

def fetch_url(
    client: httpx.Client,
    url: str,
) -> Dict[str, Any]:
    """
    Fetch an HTML/text URL.
    """

    if not validate_url(url):

        return {
            "url": url,
            "success": False,
            "status_code": None,
            "error": "invalid_url",
            "text": "",
            "title": "",
            "html": "",
        }

    last_error = None

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = client.get(
                url,
                follow_redirects=True,
            )

            content_type = (
                response.headers.get(
                    "content-type",
                    "",
                ).lower()
            )

            if response.status_code >= 400:

                return {
                    "url": str(response.url),
                    "success": False,
                    "status_code": response.status_code,
                    "error": (
                        f"http_{response.status_code}"
                    ),
                    "text": "",
                    "title": "",
                    "html": "",
                }

            if (
                "text/html" not in content_type
                and "text/plain" not in content_type
            ):

                return {
                    "url": str(response.url),
                    "success": False,
                    "status_code": response.status_code,
                    "error": (
                        "unsupported_content_type:"
                        + content_type
                    ),
                    "text": "",
                    "title": "",
                    "html": "",
                }

            html = response.text

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg",
                ]
            ):
                element.decompose()

            title = ""

            if soup.title:

                title = soup.title.get_text(
                    " ",
                    strip=True,
                )

            text = soup.get_text(
                " ",
                strip=True,
            )

            text = re.sub(
                r"\s+",
                " ",
                text,
            ).strip()

            text = text[:50000]

            return {
                "url": str(response.url),
                "success": True,
                "status_code": response.status_code,
                "error": None,
                "text": text,
                "title": title,
                "html": html,
            }

        except Exception as exc:

            last_error = str(exc)

            if attempt < MAX_RETRIES:

                time.sleep(
                    REQUEST_DELAY_SECONDS
                    * (attempt + 1)
                )

    return {
        "url": url,
        "success": False,
        "status_code": None,
        "error": (
            last_error
            or "request_failed"
        ),
        "text": "",
        "title": "",
        "html": "",
    }


# ============================================================
# PAGE RELEVANCE
# ============================================================

def page_relevance(
    url: str,
    title: str,
    text: str,
) -> int:
    """
    Score a retrieved page for research relevance.
    """

    haystack = (
        f"{url} "
        f"{title} "
        f"{text[:10000]}"
    ).lower()

    score = 0

    for keyword, weight in {
        "api": 4,
        "developer": 3,
        "authentication": 4,
        "oauth": 4,
        "authorization": 3,
        "access token": 3,
        "pricing": 2,
        "plan": 1,
        "mcp": 5,
        "webhook": 2,
        "rest": 2,
        "graphql": 2,
        "sdk": 2,
    }.items():

        if keyword in haystack:
            score += weight

    return score


# ============================================================
# CLAIM DETECTION
# ============================================================

def detect_claims(
    url: str,
    title: str,
    text: str,
) -> List[Dict[str, str]]:
    """
    Detect conservative claims from official documentation.

    No claim is created unless an explicit textual indicator
    exists in the retrieved page.
    """

    claims: List[Dict[str, str]] = []

    lower_text = text.lower()

    source_type = classify_source_type(
        url
    )

    official_auth_type = (
        "official_auth_docs"
        if source_type.startswith("official")
        else source_type
    )

    official_api_type = (
        "official_api_docs"
        if source_type.startswith("official")
        else source_type
    )

    # OAuth
    if "oauth" in lower_text:

        claims.append(
            {
                "claim": (
                    "Documentation mentions OAuth authentication."
                ),
                "url": url,
                "source_type": official_auth_type,
            }
        )

    # API key
    if any(
        pattern in lower_text
        for pattern in (
            "api key",
            "apikey",
            "x-api-key",
        )
    ):

        claims.append(
            {
                "claim": (
                    "Documentation mentions API key authentication."
                ),
                "url": url,
                "source_type": official_auth_type,
            }
        )

    # Bearer token
    if "bearer token" in lower_text:

        claims.append(
            {
                "claim": (
                    "Documentation mentions Bearer token authentication."
                ),
                "url": url,
                "source_type": official_auth_type,
            }
        )

    # REST
    if re.search(
        r"\brest(?:ful)?\b",
        lower_text,
    ):

        claims.append(
            {
                "claim": (
                    "Documentation mentions a REST API."
                ),
                "url": url,
                "source_type": official_api_type,
            }
        )

    # GraphQL
    if "graphql" in lower_text:

        claims.append(
            {
                "claim": (
                    "Documentation mentions GraphQL."
                ),
                "url": url,
                "source_type": official_api_type,
            }
        )

    # Webhooks
    if "webhook" in lower_text:

        claims.append(
            {
                "claim": (
                    "Documentation mentions webhooks."
                ),
                "url": url,
                "source_type": official_api_type,
            }
        )

    # MCP
    if (
        "model context protocol" in lower_text
        or re.search(
            r"\bmcp\b",
            lower_text,
        )
    ):

        claims.append(
            {
                "claim": (
                    "Documentation mentions MCP "
                    "(Model Context Protocol)."
                ),
                "url": url,
                "source_type": "official_mcp",
            }
        )

    # Pricing
    if (
        "/pricing" in url.lower()
        or "/plans" in url.lower()
        or "pricing" in lower_text
    ):

        claims.append(
            {
                "claim": (
                    "Documentation contains pricing "
                    "or plan information."
                ),
                "url": url,
                "source_type": "official_pricing",
            }
        )

    return claims


# ============================================================
# APP RESEARCH
# ============================================================

def research_app_sources(
    app_name: str,
) -> Dict[str, Any]:
    """
    Discover and retrieve official sources for one app.
    """

    logger.info(
        "Researching official sources for %s",
        app_name,
    )

    base_url = get_official_base_url(
        app_name
    )

    if not base_url:

        logger.warning(
            "No known official documentation domain for %s",
            app_name,
        )

        return {
            "app_name": app_name,
            "sources": [],
            "evidence": [],
            "retrieved_pages": 0,
            "research_status": "unknown",
            "errors": [
                "No known official documentation domain."
            ],
        }

    sources: List[Dict[str, Any]] = []

    evidence: List[Dict[str, str]] = []

    errors: List[str] = []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,text/plain;q=0.9,*/*;q=0.8"
        ),
    }

    with httpx.Client(
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    ) as client:

        # ----------------------------------------------------
        # 1. Fetch known official entry point
        # ----------------------------------------------------

        logger.info(
            "Fetching official entry point: %s",
            base_url,
        )

        root_result = fetch_url(
            client,
            base_url,
        )

        if not root_result["success"]:

            errors.append(
                f"{base_url}: "
                f"{root_result['error']}"
            )

        else:

            root_record = {
                "url": root_result["url"],
                "title": root_result["title"],
                "source_type": classify_source_type(
                    root_result["url"]
                ),
                "relevance_score": page_relevance(
                    root_result["url"],
                    root_result["title"],
                    root_result["text"],
                ),
            }

            sources.append(
                root_record
            )

            evidence.extend(
                detect_claims(
                    root_result["url"],
                    root_result["title"],
                    root_result["text"],
                )
            )

        # ----------------------------------------------------
        # 2. Discover links from official page
        # ----------------------------------------------------

        discovered_links: List[str] = []

        if root_result["success"]:

            discovered_links = discover_links(
                root_result["url"],
                root_result["html"],
            )

            logger.info(
                "Discovered %d relevant official links",
                len(discovered_links),
            )

        # ----------------------------------------------------
        # 3. Fetch only the most relevant links
        # ----------------------------------------------------

        for url in discovered_links:

            if len(sources) >= MAX_FETCHED_PAGES:
                break

            if any(
                source["url"] == url
                for source in sources
            ):
                continue

            logger.info(
                "Fetching discovered source: %s",
                url,
            )

            result = fetch_url(
                client,
                url,
            )

            if not result["success"]:

                errors.append(
                    f"{url}: "
                    f"{result['error']}"
                )

                continue

            sources.append(
                {
                    "url": result["url"],
                    "title": result["title"],
                    "source_type": classify_source_type(
                        result["url"]
                    ),
                    "relevance_score": page_relevance(
                        result["url"],
                        result["title"],
                        result["text"],
                    ),
                }
            )

            evidence.extend(
                detect_claims(
                    result["url"],
                    result["title"],
                    result["text"],
                )
            )

            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    # --------------------------------------------------------
    # Deduplicate evidence
    # --------------------------------------------------------

    unique_evidence = []

    seen_evidence = set()

    for item in evidence:

        key = (
            item.get("url"),
            item.get("claim"),
        )

        if key in seen_evidence:
            continue

        seen_evidence.add(key)

        unique_evidence.append(
            item
        )

    evidence = unique_evidence

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    if sources and evidence:
        status = "success"

    elif sources:
        status = "partial"

    elif errors:
        status = "failed"

    else:
        status = "unknown"

    return {
        "app_name": app_name,
        "official_base_url": base_url,
        "sources": sources[:MAX_SOURCES_PER_APP],
        "evidence": evidence,
        "retrieved_pages": len(sources),
        "research_status": status,
        "errors": errors,
    }