# Monarch Castle Technologies — SRTI

This repository's public GitHub Pages product is **SRTI-004, the Sahel Region Threat Index**: a static, transparent monitor of public security reporting about Mali, Niger, and Burkina Faso.

SRTI is a deterministic triage heuristic. It is not a verified event database, incident count, probability forecast, or military assessment. Every displayed evidence item links to its publisher.

## Run locally

```bash
python -m pip install -r "Sahel Region Threat Index (SRTI)/requirements.txt"
python "Sahel Region Threat Index (SRTI)/sahel_watch.py"
python -c "import generate_pages as gp; gp.generate_srti_page()"
python scripts/validate_srti.py
python scripts/build_pages.py
```

Serve `.pages-artifact` to test the exact deployable output:

```bash
python -m http.server 8000 --directory .pages-artifact
```

## Publication contract

- Inputs: public RSS feeds with public HTML fallback. No API account, key, email, or operator login.
- Window: publisher-dated items from the previous 72 hours. Undated items do not affect the score.
- Scoring: complete-term keyword hits, source weights, and recency decay; fixed 0–100 composite.
- Gate: minimum responding-source, dated-item, and target-country coverage. Failure exits without replacing the accepted snapshot, history, event log, or site.
- Deployment: tests, data validation, minimal-artifact build, pre-deploy HTTP check, GitHub Pages deployment, post-deploy HTTP check.

The hourly workflow uses only the repository-scoped GitHub Actions token to commit accepted public snapshots and deploy Pages. It requires no third-party secrets.

## Relevant paths

- `Sahel Region Threat Index (SRTI)/sahel_watch.py` — collector, scoring, and quality gate.
- `generate_pages.py` — pre-rendered operator page.
- `data/srti_latest.json` — current accepted snapshot and provenance.
- `data/srti_history.json` — accepted snapshot history.
- `scripts/validate_srti.py` — fail-closed data and page contract.
- `scripts/smoke_pages.py` — pre/post-deploy HTTP health check.
- `.github/workflows/` — verified update and deployment automation.

Other directories are retained research prototypes and are not represented as active capabilities on the public SRTI page.

Informational use only. Verify linked reporting before use; not financial or military advice.
