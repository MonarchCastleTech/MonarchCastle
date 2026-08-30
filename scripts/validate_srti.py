"""Fail closed when SRTI data or generated Pages output violates its contract."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "Sahel Region Threat Index (SRTI)" / "index.html"
ALLOWED_SOURCE_STATES = {"ok", "empty", "unreachable"}
ALLOWED_REGIONS = {"mali", "niger", "burkina_faso", "sahel"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_aware(value: object, field: str) -> datetime:
    require(isinstance(value, str) and value, f"{field} must be a timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, f"{field} must include timezone")
    return parsed


def is_https(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_data(latest: dict, history: list) -> None:
    require(latest.get("schema_version") == 2, "unsupported snapshot schema")
    require(latest.get("methodology_version") == "2.0", "unsupported methodology")
    fetched_at = parse_aware(latest.get("fetched_at"), "fetched_at")
    parse_aware(latest.get("content_latest_at"), "content_latest_at")

    score = latest.get("score")
    require(isinstance(score, (int, float)) and 0 <= score <= 100, "score out of range")
    require(latest.get("risk_level") in {"LOW", "GUARDED", "ELEVATED", "HIGH", "CRITICAL"}, "invalid risk level")

    components = latest.get("components")
    weights = latest.get("weights")
    require(isinstance(components, dict) and components, "components missing")
    require(isinstance(weights, dict) and weights.keys() == components.keys(), "weights mismatch")
    require(all(isinstance(value, (int, float)) and 0 <= value <= 100 for value in components.values()), "component out of range")
    require(abs(sum(float(value) for value in weights.values()) - 1.0) < 0.001, "weights must sum to one")

    sources = latest.get("sources")
    require(isinstance(sources, list) and len(sources) >= 4, "source ledger too small")
    require(len({source.get("name") for source in sources}) == len(sources), "duplicate source names")
    for source in sources:
        require(is_https(source.get("url")), f"source URL must be HTTPS: {source.get('name')}")
        require(source.get("status") in ALLOWED_SOURCE_STATES, f"invalid source state: {source.get('name')}")
        require(set(source.get("regions") or []).issubset(ALLOWED_REGIONS), f"invalid source region: {source.get('name')}")

    gate = latest.get("quality_gate")
    require(isinstance(gate, dict) and gate.get("passed") is True, "snapshot did not pass quality gate")
    require(gate.get("reachable_sources", 0) >= gate.get("criteria", {}).get("minimum_reachable_sources", 999), "source gate inconsistent")
    require(len(gate.get("covered_regions") or []) >= gate.get("criteria", {}).get("minimum_target_countries", 999), "country gate inconsistent")
    require(gate.get("dated_items", 0) >= gate.get("criteria", {}).get("minimum_dated_items", 999), "dated-item gate inconsistent")

    forbidden_keys = {"api_key", "token", "secret", "email", "account"}
    require(not forbidden_keys.intersection(latest), "account or secret field exposed")
    for item in latest.get("top_headlines") or []:
        require(is_https(item.get("link")), "headline URL must be HTTPS")
        require(set(item.get("regions") or []).issubset(ALLOWED_REGIONS), "headline region invalid")
        parse_aware(item.get("published_at"), "headline published_at")

    require(isinstance(history, list) and history, "history missing")
    history_times = [parse_aware(item.get("timestamp"), "history timestamp") for item in history]
    require(history_times == sorted(history_times), "history timestamps not monotonic")
    require(history_times[-1] == fetched_at, "latest snapshot and history disagree")
    require(history[-1].get("methodology_version") == latest.get("methodology_version"), "latest history methodology mismatch")


def validate_html(path: Path, expected_asset_prefix: str) -> None:
    markup = path.read_text(encoding="utf-8")
    for marker in (
        "SRTI / PUBLIC OSINT MONITOR",
        "data-collected-at=",
        "Source ledger",
        "Quality gate",
        "Not military advice",
        f'href="{expected_asset_prefix}/srti.css?v=2.0"',
        f'src="{expected_asset_prefix}/mc-mark.png"',
    ):
        require(marker in markup, f"{path.name} missing marker: {marker}")
    for banned in ("Sources Live", "Commercial Access", "$299", "Contact Sales", "real-time"):
        require(banned not in markup, f"{path.name} contains unsupported copy: {banned}")


def validate(root: Path = ROOT) -> None:
    latest = json.loads((root / "data/srti_latest.json").read_text(encoding="utf-8"))
    history = json.loads((root / "data/srti_history.json").read_text(encoding="utf-8"))
    validate_data(latest, history)
    validate_html(root / "index.html", "assets")
    validate_html(root / "Sahel Region Threat Index (SRTI)" / "index.html", "../assets")
    for asset in ("mc-mark.png", "srti.css", "srti.js"):
        require((root / "assets" / asset).is_file(), f"missing asset: {asset}")


if __name__ == "__main__":
    validate()
    print("[OK] SRTI data and Pages output validated")
