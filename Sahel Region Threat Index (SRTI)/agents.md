# SAHEL REGION THREAT INDEX - AGENT CONTEXT
> **Role**: You are the Africa Regional Analyst for the Sahel module.

---

## 📊 MODULE: Sahel Watch
**Code**: SRTI | **Division**: MCDI | **Status**: ACTIVE PUBLIC PAGES PRODUCT

---

## 🎯 OBJECTIVE

Monitor public security reporting about Mali, Niger, and Burkina Faso. Publish a deterministic triage score with source, timestamp, methodology, limitation, and freshness evidence. Never present the score as verified intelligence, an incident count, or a coup probability.

## RSS-FIRST POLICY
Use RSS feeds and lightweight web scraping from Sahel-region news sites whenever possible. Do not require APIs for SRTI data collection.

---

## 📁 FILES TO CREATE

| File | Purpose |
|------|---------|
| `sahel_watch.py` | RSS-first OSINT fetcher with Sahel filters (no API) |
| `sahel_data.csv` | Processed events |
| `requirements.txt` | Dependencies |
| `../data/srti_latest.json` | Accepted snapshot and provenance |
| `../generate_pages.py` | Static operator page generator |

---

## 🔧 IMPLEMENTATION REQUIREMENTS

### 1. Data Pipeline
- Public RSS first; public HTML headings only as transport fallback.
- No third-party account, email, API key, or private feed.
- Exclude undated, future-dated, and out-of-window items from scoring.
- Match complete terms so `Niger` does not match `Nigeria` and `Mali` does not match `Somali`.
- Publish only after transport, dated-item, and target-country gates pass.

### 2. Scoring
- Deterministic keyword, source-weight, and recency heuristic.
- Normalized 0–100 components and composite; weights sum to 1.
- No generative classification and no predictive probability.

### 3. Visualization
- Static, keyboard-accessible operator page.
- Fixed-axis accepted-history chart, filterable evidence queue, source ledger, provenance, and freshness state.
- Correct transparent Monarch Castle mark from `assets/mc-mark.png`.

---

## 🚀 RUN COMMANDS

```bash
# Fetch and analyze
python sahel_watch.py

# Generate and validate static Pages output
python -c "import generate_pages as gp; gp.generate_srti_page()"
python scripts/validate_srti.py
```

---

## 🔐 ACCESS

No credentials. SRTI uses only public publisher endpoints and the repository-scoped GitHub Actions token supplied by GitHub for accepted-snapshot commits and Pages deployment.

---

## 🔗 INTEGRATION

SRTI is the repository root GitHub Pages product. Other research modules are not exposed as active SRTI capabilities.

---

**Dependencies**: requests, beautifulsoup4
