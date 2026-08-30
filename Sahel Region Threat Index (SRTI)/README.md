# Sahel Region Threat Index (SRTI)

RSS-first OSINT pipeline for Mali, Niger, and Burkina Faso. It produces a static
site with precomputed scores and source evidence (no client-side data fetching).

## Local run
```bash
python "Sahel Region Threat Index (SRTI)/sahel_watch.py"
python -c "import generate_pages as gp; gp.generate_srti_page()"
python scripts/validate_srti.py
```

## Outputs
- `data/srti_latest.json`: accepted score, components, source ledger, provenance, and gate result.
- `data/srti_history.json`: hourly history for charting and trends.
- `Sahel Region Threat Index (SRTI)/sahel_data.csv`: event log (trimmed to last 2000 rows).
- `Sahel Region Threat Index (SRTI)/index.html`: static site output.

## GitHub Actions
The workflow in `.github/workflows/srti_hourly.yml` runs hourly against public
feeds without third-party credentials. It publishes only when coverage gates,
tests, validation, and pre-deploy health checks pass. A failed collection keeps
the last-known-good site unchanged. The deploy is checked again over HTTP.
