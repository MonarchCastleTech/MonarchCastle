"""
Sahel Region Threat Index (SRTI)
RSS-first OSINT pipeline for Mali, Niger, and Burkina Faso.
Outputs:
  - data/srti_latest.json
  - data/srti_history.json
  - Sahel Region Threat Index (SRTI)/sahel_data.csv
"""
from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SRTI_DIR = Path(__file__).resolve().parent
EVENT_LOG_CSV = SRTI_DIR / "sahel_data.csv"
LATEST_JSON = DATA_DIR / "srti_latest.json"
HISTORY_JSON = DATA_DIR / "srti_history.json"

USER_AGENT = "MonarchCastleSRTI/1.0 (+https://monarchcastle.tech)"
HEADERS = {"User-Agent": USER_AGENT}

WINDOW_HOURS = 72
HISTORY_LIMIT = 24 * 30
MAX_LOG_ROWS = 2000
MIN_REACHABLE_SOURCES = 4
MIN_REGION_COVERAGE = 2
MIN_DATED_ITEMS = 3
METHODOLOGY_VERSION = "2.0"
FETCH_TIMEOUT_SECONDS = 12
MAX_FETCH_WORKERS = 6

SOURCES = [
    {
        "name": "ReliefWeb - Mali",
        "rss": "https://reliefweb.int/rss?search=country%3AMali",
        "html": "https://reliefweb.int/country/mli",
        "region_focus": True,
        "regions": ["mali"],
        "weight": 0.9,
    },
    {
        "name": "ReliefWeb - Niger",
        "rss": "https://reliefweb.int/rss?search=country%3ANiger",
        "html": "https://reliefweb.int/country/ner",
        "region_focus": True,
        "regions": ["niger"],
        "weight": 0.9,
    },
    {
        "name": "ReliefWeb - Burkina Faso",
        "rss": "https://reliefweb.int/rss?search=country%3ABurkina%20Faso",
        "html": "https://reliefweb.int/country/bfa",
        "region_focus": True,
        "regions": ["burkina_faso"],
        "weight": 0.9,
    },
    {
        "name": "MaliWeb",
        "rss": "https://www.maliweb.net/feed",
        "html": "https://www.maliweb.net/",
        "region_focus": True,
        "regions": ["mali"],
        "weight": 0.8,
    },
    {
        "name": "LeFaso",
        "rss": "https://lefaso.net/spip.php?page=backend",
        "html": "https://lefaso.net/",
        "region_focus": True,
        "regions": ["burkina_faso"],
        "weight": 0.8,
    },
    {
        "name": "ActuNiger",
        "rss": "https://www.actuniger.com/feed/",
        "html": "https://www.actuniger.com/",
        "region_focus": True,
        "regions": ["niger"],
        "weight": 0.8,
    },
    {
        "name": "BBC Africa",
        "rss": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "html": "https://www.bbc.com/news/world/africa",
        "region_focus": False,
        "regions": [],
        "weight": 0.6,
    },
    {
        "name": "UN News Africa",
        "rss": "https://news.un.org/feed/subscribe/en/news/region/africa/feed/rss.xml",
        "html": "https://news.un.org/en/news/region/africa",
        "region_focus": False,
        "regions": [],
        "weight": 0.6,
    },
    {
        "name": "Crisis Group",
        "rss": "https://www.crisisgroup.org/rss.xml",
        "html": "https://www.crisisgroup.org/africa",
        "region_focus": False,
        "regions": [],
        "weight": 0.6,
    },
    {
        "name": "France 24 - Africa",
        "rss": "https://www.france24.com/en/africa/rss",
        "html": "https://www.france24.com/en/africa/",
        "region_focus": False,
        "regions": [],
        "weight": 0.7,
    },
    {
        "name": "AllAfrica - Mali",
        "rss": "https://allafrica.com/tools/headlines/rdf/mali/headlines.rdf",
        "html": "https://allafrica.com/mali/",
        "region_focus": True,
        "regions": ["mali"],
        "weight": 0.6,
    },
    {
        "name": "AllAfrica - Niger",
        "rss": "https://allafrica.com/tools/headlines/rdf/niger/headlines.rdf",
        "html": "https://allafrica.com/niger/",
        "region_focus": True,
        "regions": ["niger"],
        "weight": 0.6,
    },
    {
        "name": "AllAfrica - Burkina Faso",
        "rss": "https://allafrica.com/tools/headlines/rdf/burkinafaso/headlines.rdf",
        "html": "https://allafrica.com/burkinafaso/",
        "region_focus": True,
        "regions": ["burkina_faso"],
        "weight": 0.6,
    },
]

REGION_KEYWORDS = {
    "mali": ["mali", "bamako", "gao", "menaka"],
    "niger": ["niger", "niamey", "tillaberi", "agadez"],
    "burkina_faso": ["burkina", "burkina faso", "ouagadougou"],
    "sahel": ["sahel"],
}



CONFLICT_KEYWORDS = [
    "attack",
    "ambush",
    "raid",
    "clash",
    "battle",
    "offensive",
    "assault",
    "explosion",
    "armed group",
    "gunmen",
]

CIVILIAN_KEYWORDS = [
    "civilian",
    "massacre",
    "killed",
    "dead",
    "fatal",
    "abducted",
    "kidnapped",
    "displaced",
    "refugee",
    "camp",
]

EXTREMIST_KEYWORDS = [
    "isis",
    "islamic state",
    "isgs",
    "jnim",
    "al qaeda",
    "aqim",
    "boko haram",
]


BUCKETS = {
    "conflict_intensity": {
        "keywords": CONFLICT_KEYWORDS + EXTREMIST_KEYWORDS,
        "multiplier": 1.4,
        "scale": 12,
        "weight": 0.5,
    },
    "civilian_risk": {
        "keywords": CIVILIAN_KEYWORDS,
        "multiplier": 1.8,
        "scale": 14,
        "weight": 0.2,
    },
}

def utc_now() -> datetime:
    return datetime.now(timezone.utc)



def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def extract_text(node: ET.Element, names: List[str]) -> str:
    for child in list(node):
        if local_name(child.tag) in names and child.text:
            return child.text.strip()
    return ""


def extract_link(node: ET.Element) -> str:
    for child in list(node):
        if local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
            if child.text:
                return child.text.strip()
    return ""


def fetch_url(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=FETCH_TIMEOUT_SECONDS)
        if resp.status_code >= 400:
            return None
        return resp.content
    except requests.RequestException:
        return None


def parse_rss(content: bytes) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return items

    if local_name(root.tag) == "rss":
        channel = next((c for c in root if local_name(c.tag) == "channel"), None)
        if channel is None:
            return items
        for item in [c for c in channel if local_name(c.tag) == "item"]:
            title = extract_text(item, ["title"])
            link = extract_text(item, ["link"]) or extract_link(item)
            summary = extract_text(item, ["description", "summary"])
            pub = extract_text(item, ["pubdate", "date", "dc:date"])
            items.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": pub,
                }
            )
        return items

    if local_name(root.tag) == "feed":
        for entry in [c for c in root if local_name(c.tag) == "entry"]:
            title = extract_text(entry, ["title"])
            link = extract_link(entry)
            summary = extract_text(entry, ["summary", "content"])
            pub = extract_text(entry, ["updated", "published"])
            items.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": pub,
                }
            )
    return items


def scrape_headlines(html: bytes, limit: int = 12) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for tag in soup.find_all(["h1", "h2", "h3"], limit=60):
        text = tag.get_text(strip=True)
        if not text or len(text) < 6:
            continue
        link = ""
        anchor = tag.find("a")
        if anchor and anchor.get("href"):
            link = anchor["href"]
        candidates.append({"title": text, "link": link, "summary": "", "published": ""})
    return candidates[:limit]


def collect_source(source: Dict[str, object]) -> Tuple[Dict[str, object], List[Dict[str, str]], str]:
    """Collect one source; callers may run independent sources concurrently."""
    items: List[Dict[str, str]] = []
    status = "ok"
    rss_content = fetch_url(str(source["rss"]))
    if rss_content:
        items = parse_rss(rss_content)
    if not items and source.get("html"):
        html_content = fetch_url(str(source["html"]))
        if html_content:
            items = scrape_headlines(html_content)
        else:
            status = "unreachable"
    if not items and status != "unreachable":
        status = "empty"
    return source, items, status


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def match_keywords(text: str, keywords: List[str]) -> List[str]:
    return [keyword for keyword in keywords if keyword_present(text, keyword)]


def keyword_present(text: str, keyword: str) -> bool:
    """Match complete terms, preventing Mali/Somali and Niger/Nigeria collisions."""
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def region_match(text: str) -> List[str]:
    return [
        region
        for region, keywords in REGION_KEYWORDS.items()
        if any(keyword_present(text, keyword) for keyword in keywords)
    ]


def safe_http_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return value


def recency_weight(published: datetime, now: datetime) -> float:
    age_hours = max(0.0, (now - published).total_seconds() / 3600)
    if age_hours > WINDOW_HOURS:
        return 0.0
    return max(0.35, 1 - (age_hours / WINDOW_HOURS))


def score_item(
    text: str,
    published: datetime,
    source_weight: float,
    now: datetime,
) -> Tuple[float, Dict[str, float], List[str], List[str]]:
    normalized = normalize_text(text)
    tags = []
    region_hits = region_match(normalized)
    bucket_scores: Dict[str, float] = {}
    decay = recency_weight(published, now)
    for bucket_name, config in BUCKETS.items():
        hits = match_keywords(normalized, config["keywords"])
        if hits:
            tags.append(bucket_name)
        bucket_scores[bucket_name] = min(3, len(hits)) * config["multiplier"] * source_weight * decay
    total_score = sum(bucket_scores.values())
    return total_score, bucket_scores, tags, region_hits


def load_existing_links() -> set:
    if not EVENT_LOG_CSV.exists():
        return set()
    links = set()
    with EVENT_LOG_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = (row.get("link") or "").strip()
            if link:
                links.add(link)
    return links


def append_event_log(rows: List[Dict[str, str]]) -> None:
    file_exists = EVENT_LOG_CSV.exists()
    cleaned_rows = [
        {k: (str(v).strip() if v is not None else "") for k, v in r.items()}
        for r in rows
    ]
    with EVENT_LOG_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "fetched_at",
                "published_at",
                "source",
                "title",
                "link",
                "regions",
                "tags",
                "score",
            ],
            lineterminator="\n",
        )
        if not file_exists:
            writer.writeheader()
        writer.writerows(cleaned_rows)

    if EVENT_LOG_CSV.exists():
        with EVENT_LOG_CSV.open("r", encoding="utf-8") as f:
            lines = [line.rstrip("\r\n") + "\n" for line in f]
        if len(lines) > MAX_LOG_ROWS + 1:
            header = lines[0]
            trimmed = lines[-MAX_LOG_ROWS:]
            with EVENT_LOG_CSV.open("w", encoding="utf-8", newline="") as f:
                f.write(header)
                f.writelines(trimmed)


def load_history() -> List[Dict[str, object]]:
    if not HISTORY_JSON.exists():
        return []
    with HISTORY_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_history(entries: List[Dict[str, object]]) -> None:
    atomic_write_json(HISTORY_JSON, entries)


def atomic_write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    temporary.replace(path)


def normalize_bucket(raw: float, scale: float) -> float:
    return max(0.0, min(100.0, raw * scale))


def classify_score(score: float) -> str:
    if score < 20:
        return "LOW"
    if score < 40:
        return "GUARDED"
    if score < 60:
        return "ELEVATED"
    if score < 80:
        return "HIGH"
    return "CRITICAL"


def evaluate_quality_gate(
    source_status: List[Dict[str, object]], dated_items: int
) -> Dict[str, object]:
    reachable = [source for source in source_status if source.get("status") == "ok"]
    covered_regions = {
        region
        for source in reachable
        if int(source.get("eligible_items", 0)) > 0
        for region in source.get("regions", [])
        if region in {"mali", "niger", "burkina_faso"}
    }
    reasons = []
    if len(reachable) < MIN_REACHABLE_SOURCES:
        reasons.append(
            f"only {len(reachable)} sources responded; need {MIN_REACHABLE_SOURCES}"
        )
    if len(covered_regions) < MIN_REGION_COVERAGE:
        reasons.append(
            f"only {len(covered_regions)} target countries covered; need {MIN_REGION_COVERAGE}"
        )
    if dated_items < MIN_DATED_ITEMS:
        reasons.append(f"only {dated_items} dated items; need {MIN_DATED_ITEMS}")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "reachable_sources": len(reachable),
        "total_sources": len(source_status),
        "covered_regions": sorted(covered_regions),
        "dated_items": dated_items,
        "criteria": {
            "minimum_reachable_sources": MIN_REACHABLE_SOURCES,
            "minimum_target_countries": MIN_REGION_COVERAGE,
            "minimum_dated_items": MIN_DATED_ITEMS,
        },
    }


def main() -> None:
    now = utc_now()
    existing_links = load_existing_links()
    all_items = []
    source_status = []

    source_status_by_name = {}
    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as executor:
        collected_sources = executor.map(collect_source, SOURCES)
        for source, items, status in collected_sources:
            all_items.extend([(source, item) for item in items])
            source_record = {
                "name": source["name"],
                "url": source["rss"],
                "status": status,
                "items": len(items),
                "eligible_items": 0,
                "regions": source.get("regions", []),
            }
            source_status.append(source_record)
            source_status_by_name[source["name"]] = source_record

    event_rows = []
    scored_items = []
    raw_buckets = {key: 0.0 for key in BUCKETS}
    seen_items = set()
    dated_items = 0
    evaluated_items = 0
    newest_content_at: Optional[datetime] = None

    for source, item in all_items:
        title = (item.get("title") or "").strip()
        summary = (item.get("summary") or "").strip()
        link = (item.get("link") or "").strip()
        if link:
            base_url = source.get("html") or source.get("rss")
            link = safe_http_url(urljoin(base_url, link))
        published = parse_datetime(item.get("published"))
        if published is None:
            continue
        age_hours = (now - published).total_seconds() / 3600
        if age_hours < -2 or age_hours > WINDOW_HOURS:
            continue
        dated_items += 1
        source_status_by_name[source["name"]]["eligible_items"] += 1

        combined = f"{title} {summary}".strip()
        combined = strip_html(combined)
        if not combined:
            continue

        normalized = normalize_text(combined)
        region_hits = sorted(set(region_match(normalized) + source.get("regions", [])))
        if not region_hits:
            continue
        evaluated_items += 1
        if newest_content_at is None or published > newest_content_at:
            newest_content_at = published

        dedupe_key = link or re.sub(r"[^a-z0-9]+", " ", normalized).strip()
        if dedupe_key in seen_items:
            continue
        seen_items.add(dedupe_key)

        total_score, bucket_scores, tags, _ = score_item(
            combined,
            published,
            source["weight"],
            now,
        )

        if total_score <= 0:
            continue

        for bucket_name, value in bucket_scores.items():
            raw_buckets[bucket_name] += value

        scored_item = {
            "title": title,
            "link": link,
            "source": source["name"],
            "published_at": published.isoformat(),
            "score": round(total_score, 2),
            "tags": tags,
            "regions": region_hits,
        }
        scored_items.append(scored_item)

        if link and link in existing_links:
            continue

        event_rows.append(
            {
                "fetched_at": now.isoformat(),
                "published_at": published.isoformat(),
                "source": source["name"],
                "title": title,
                "link": link,
                "regions": ",".join(region_hits),
                "tags": ",".join(tags),
                "score": f"{total_score:.2f}",
            }
        )

    quality_gate = evaluate_quality_gate(source_status, dated_items)
    if not quality_gate["passed"]:
        print("[HOLD] Collection failed quality gate; last-known-good snapshot retained")
        for reason in quality_gate["reasons"]:
            print(f"[HOLD] {reason}")
        raise SystemExit(2)

    normalized_buckets = {}
    for bucket_name, raw_value in raw_buckets.items():
        normalized_buckets[bucket_name] = round(
            normalize_bucket(raw_value, BUCKETS[bucket_name]["scale"]),
            1,
        )

    raw_weights = {key: BUCKETS[key]["weight"] for key in BUCKETS}
    weight_total = sum(raw_weights.values()) or 1.0
    normalized_weights = {
        key: round(value / weight_total, 4) for key, value in raw_weights.items()
    }
    overall_score = 0.0
    for bucket_name, score in normalized_buckets.items():
        overall_score += score * normalized_weights[bucket_name]
    overall_score = round(overall_score, 1)
    risk_level = classify_score(overall_score)

    scored_items.sort(key=lambda x: x["score"], reverse=True)
    top_items = scored_items[:8]

    history = load_history()
    history.append(
        {
            "timestamp": now.isoformat(),
            "methodology_version": METHODOLOGY_VERSION,
            "score": overall_score,
            "risk_level": risk_level,
            "components": normalized_buckets,
            "items": len(scored_items),
        }
    )
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]

    latest = {
        "schema_version": 2,
        "methodology_version": METHODOLOGY_VERSION,
        "fetched_at": now.isoformat(),
        "content_latest_at": newest_content_at.isoformat() if newest_content_at else None,
        "window_hours": WINDOW_HOURS,
        "score": overall_score,
        "risk_level": risk_level,
        "components": normalized_buckets,
        "weights": normalized_weights,
        "items_count": len(scored_items),
        "items_evaluated": evaluated_items,
        "sources": source_status,
        "top_headlines": top_items,
        "quality_gate": quality_gate,
        "provenance": {
            "collection": "Public RSS feeds with public HTML fallback; no API accounts or keys.",
            "scoring": "Deterministic keyword and recency heuristic; no model-generated classifications.",
            "publication": "Accepted snapshots only; failed collection gates retain the prior snapshot.",
        },
    }

    atomic_write_json(LATEST_JSON, latest)
    save_history(history)
    if event_rows:
        append_event_log(event_rows)

    print(f"[OK] SRTI score {overall_score} ({risk_level}) from {len(scored_items)} items")


if __name__ == "__main__":
    main()
