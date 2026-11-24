"""Find links to maintenance guides without Groq or reading whole manuals.

Search is intentionally broad across vehicle makes. It does NOT contain a table
of supported car models or manufacturer maintenance intervals.

Search engines may block automated clients; failed lookups receive a clearly
labeled AAA general-maintenance fallback. No vehicle intervals are invented.
"""

from __future__ import annotations

import html
import re
import time
import xml.etree.ElementTree as ET
from functools import lru_cache
from urllib.parse import parse_qs, unquote, urlsplit

AAA_GUIDE_URL = "https://www.aaa.com/autorepair/articles/time-stamped-car-maintenance-checklist"

# Brand WEBSITE aliases only, NOT supported vehicle model names/specifications.
# Exact-match checks below protect against a domain such as fake-toyota.com.
# Makes not listed here are still searched and can be verified by domain name.
BRAND_SITE_ALIASES = {
    "volkswagen": {"vw.com"},
    "mercedesbenz": {"mbusa.com"},
    "bmw": {"bmwusa.com"},
    "nissan": {"nissanusa.com"},
    "mazda": {"mazdausa.com"},
    "hyundai": {"hyundaiusa.com"},
    "infiniti": {"infinitiusa.com", "nissanusa.com"},
    "ram": {"ramtrucks.com", "mopar.com"},
    "jeep": {"jeep.com", "mopar.com"},
    "dodge": {"dodge.com", "mopar.com"},
    "chrysler": {"chrysler.com", "mopar.com"},
    "acura": {"acura.com", "honda.com"},
    "lexus": {"lexus.com", "toyota.com"},
    "lincoln": {"lincoln.com", "ford.com", "fordservicecontent.com"},
    "chevrolet": {"chevrolet.com", "gm.com"},
    "gmc": {"gmc.com", "gm.com"},
    "cadillac": {"cadillac.com", "gm.com"},
    "buick": {"buick.com", "gm.com"},
    "landrover": {"landrover.com"},
    "volvo": {"volvocars.com"},
    "ford": {"fordservicecontent.com"},
}

TRUSTED_THIRD_PARTY = {"manualslib.com", "manuals.co", "carmanualsonline.info"}

# This list describes generic website terminology, never vehicle service intervals.
MAINTENANCE_TERMS = (
    "maintenance", "service schedule", "scheduled service", "warranty and maintenance",
    "warranty & maintenance", "owners manual", "owner's manual", "owner manual",
    "maintenance guide", "service manual", "service booklet", "service interval",
)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _registered_domain(host: str) -> str:
    """Small common-domain check; never trusts arbitrary subdomain substrings."""
    parts = host.lower().strip(".").split(".")
    if len(parts) < 2:
        return ""
    idx = -2
    if len(parts) >= 3 and parts[-2] in {"com", "co", "org", "net", "gov"} and len(parts[-1]) == 2:
        idx = -3
    return ".".join(parts[idx:]) if idx == -2 else ".".join(parts[-3:])


def _is_approved_brand_domain(url: str, make: str) -> bool:
    try:
        p = urlsplit(url)
        if p.scheme != "https" or p.username or p.password:
            return False
        host = (p.hostname or "").lower()
        reg = _registered_domain(host)
        if not reg:
            return False
        aliases = BRAND_SITE_ALIASES.get(_norm(make), set())
        if reg in aliases:
            return True
        # Examples: toyota.com, nissanusa.com, vw.com if make is Volkswagen
        site_name = _norm(reg.rsplit(".", 1)[0])
        brand_name = _norm(make)
        known_suffixes = (
            "", "usa", "global", "motors", "motor", "cars", "auto",
            "automotive", "trucks", "service", "owners", "servicecontent"
        )
        return len(brand_name) >= 3 and any(site_name == brand_name + suffix for suffix in known_suffixes)
    except ValueError:
        return False


def _is_trusted_copy(url: str) -> bool:
    try:
        p = urlsplit(url)
        if p.scheme != "https" or p.username or p.password:
            return False
        return _registered_domain(p.hostname or "") in TRUSTED_THIRD_PARTY
    except ValueError:
        return False


def _unwrap_search_url(url: str) -> str:
    """Reject search-engine redirects rather than displaying them as a manual."""
    try:
        p = urlsplit(url)
        if p.scheme not in ("https", "http") or not p.hostname:
            return ""
        if p.hostname.lower().endswith(("google.com", "bing.com", "duckduckgo.com")):
            params = parse_qs(p.query)
            for name in ("url", "uddg", "q"):
                target = unquote(params.get(name, [""])[0])
                if target.startswith("https://") and target != url:
                    return target
            return ""
        return url
    except ValueError:
        return ""


def _score_hit(item: dict, year: int, make: str, model: str) -> dict | None:
    """Rank search hits conservatively, without downloading or parsing a manual."""
    url = _unwrap_search_url(str(item.get("href") or item.get("url") or item.get("link") or ""))
    if not url.startswith("https://"):
        return None
    title = html.unescape(re.sub(r"<[^>]+>", " ", str(item.get("title") or ""))).strip()
    snippet = html.unescape(re.sub(r"<[^>]+>", " ", str(item.get("body") or item.get("description") or ""))).strip()
    try:
        path = unquote(urlsplit(url).path)
    except ValueError:
        return None

    candidate = _norm(" ".join((title, snippet, path)))
    title_path = _norm(title + " " + path)
    model_token = _norm(model)
    make_token = _norm(make)
    y = str(year)
    if not model_token or model_token not in candidate:
        return None
    official = _is_approved_brand_domain(url, make)
    copy = _is_trusted_copy(url)
    if not (official or copy):
        return None
    exact_year = y in candidate
    # Never show an explicitly DIFFERENT year as a model-year match.
    # A yearless manufacturer portal can still be useful, but must be clearly
    # labeled as a general portal where the customer selects their year.
    other_years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", title + " " + path))
    if other_years and y not in other_years:
        return None
    if not exact_year and not official:
        return None

    full_text = (title + " " + snippet + " " + path).lower()
    if not any(term in full_text for term in MAINTENANCE_TERMS):
        return None

    # Year in title/URL, not just generic snippets, is a stronger match.
    score = (100 if official else 35) if exact_year else 55
    score += 25 if y in title_path else 0
    score += 20 if model_token in title_path else 0
    score += 20 if any(term in full_text for term in ("maintenance schedule", "scheduled maintenance", "maintenance guide", "warranty and maintenance")) else 0
    score += 10 if path.lower().endswith(".pdf") else 0
    if "owner" in full_text and "maintenance" not in full_text and "schedule" not in full_text:
        score -= 10

    return {
        "title": title or f"{year} {make} {model} maintenance guide",
        "url": url,
        "source_type": ("likely_official" if exact_year else "manufacturer_portal") if official else "third_party_copy",
        "source_label": ("Likely manufacturer website" if exact_year else "Manufacturer portal — choose the correct year") if official else "Third-party manual copy — verify",
        "description": snippet[:240],
        "score": score,
    }


def _ddgs_results(query: str) -> list[dict]:
    try:
        from ddgs import DDGS
        # Keep each lookup bounded. Unavailable search services should not break the app.
        with DDGS(timeout=9) as search:
            return list(search.text(query, max_results=9, backend="auto"))
    except Exception:
        return []


def _bing_rss_results(query: str) -> list[dict]:
    try:
        import requests
        response = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "format": "rss"},
            headers={"User-Agent": "Mozilla/5.0 (compatible; PocketMechanic/1.0)"},
            timeout=9,
        )
        response.raise_for_status()
        if len(response.content) > 400_000:
            return []
        root = ET.fromstring(response.content)
        return [
            {
                "title": node.findtext("title") or "",
                "href": node.findtext("link") or "",
                "body": node.findtext("description") or "",
            }
            for node in root.findall("./channel/item")[:10]
        ]
    except Exception:
        return []


@lru_cache(maxsize=192)
def _lookup_cached(year: int, make: str, model: str, cache_hour: int) -> tuple[dict, ...]:
    queries = (
        f'"{year}" "{make}" "{model}" maintenance schedule owners manual',
        f'{year} {make} {model} official warranty maintenance guide pdf',
        f'{year} {make} {model} manufacturer service maintenance booklet',
    )
    hits: list[dict] = []
    for i, query in enumerate(queries):
        found = _ddgs_results(query)
        # Bing RSS helps when a DDGS search backend is blocked or not returning
        # manufacturer results. Do not rely on one provider to work every time.
        if not found or i == 0:
            found += _bing_rss_results(query)
        for hit in found:
            scored = _score_hit(hit, year, make, model)
            if scored:
                hits.append(scored)
        # Enough high-quality official results: stop requesting search engines.
        if len([h for h in hits if h["source_type"] == "likely_official"]) >= 4:
            break

    seen: set[str] = set()
    unique: list[dict] = []
    for hit in sorted(hits, key=lambda x: x["score"], reverse=True):
        # Strip fragments; allow query parameters on real manufacturer pages.
        target = hit["url"].split("#", 1)[0]
        if target not in seen:
            seen.add(target)
            unique.append({k: v for k, v in hit.items() if k != "score"})
    # Prefer manufacturer links. Only use independently hosted copies when no
    # manufacturer link was discovered.
    official = [h for h in unique if h["source_type"] in ("likely_official", "manufacturer_portal")]
    copies = [h for h in unique if h["source_type"] == "third_party_copy"]
    return tuple(official[:5] if official else copies[:3])


def find_maintenance_manuals(year: int, make: str, model: str) -> dict:
    year = int(year)
    make = make.strip()[:100]
    model = model.strip()[:100]
    results = list(_lookup_cached(year, make, model, int(time.time() // 3600)))
    return {
        "vehicle_name": f"{year} {make} {model}",
        "manuals": results,
        "automatic_results_found": bool(results),
        "aaa_fallback": {
            "title": "AAA's general car maintenance checklist",
            "url": AAA_GUIDE_URL,
            "note": "General guidance only; not a substitute for your vehicle's manufacturer schedule.",
        },
        "message": (
            "These are matching manual or maintenance-guide links. Open the source "
            "and check the exact vehicle, engine, and schedule before saving a reminder."
            if results else
            "Automatic searches did not return a sufficiently verified link. "
            "This does NOT mean your vehicle has no manual. "
            "AAA general guidance is available as a fallback."
        ),
    }
