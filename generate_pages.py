"""
MONARCH CASTLE - STATIC PAGE GENERATOR
Reads JSON data and generates static HTML pages with embedded data.
No JavaScript data fetching - everything is pre-rendered.
"""

import html as html_lib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"


def load_json(filename):
    """Load JSON data file"""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def generate_sentiment_page():
    """Generate Cloudy & Shiny sentiment page with real data"""
    data = load_json("sentiment_index.json")
    crypto = load_json("crypto_fear_greed.json")
    
    if not data:
        print("[ERROR] No sentiment data found")
        return
    
    score = data["composite_score"]
    classification = data["classification"]
    condition = data["condition"]
    
    # Generate history rows
    crypto_history = ""
    if crypto and "history" in crypto:
        for h in crypto["history"][:7]:
            crypto_history += f'<tr><td>{h["date"]}</td><td>{h["value"]}</td><td>{h["classification"]}</td></tr>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSI-008 | Market Sentiment Index</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0a0a0a; --surface: #141414; --border: #262626; --text: #fafafa; --text-secondary: #737373; --accent: #f59e0b; --success: #10b981; --danger: #ef4444; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}
        header {{ padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(10,10,10,0.9); backdrop-filter: blur(12px); z-index: 100; }}
        header .container {{ display: flex; justify-content: space-between; align-items: center; }}
        .breadcrumb {{ display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }}
        .breadcrumb a {{ color: var(--text-secondary); text-decoration: none; }}
        .status-badge {{ display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.2); border-radius: 6px; font-size: 12px; font-weight: 500; color: var(--success); }}
        .status-dot {{ width: 6px; height: 6px; background: var(--success); border-radius: 50%; animation: blink 2s ease-in-out infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        .hero {{ padding: 80px 0 60px; border-bottom: 1px solid var(--border); }}
        .module-id {{ font-size: 12px; font-weight: 600; color: var(--accent); letter-spacing: 0.1em; margin-bottom: 16px; font-family: monospace; }}
        .hero h1 {{ font-size: 42px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 16px; }}
        .hero p {{ font-size: 18px; color: var(--text-secondary); max-width: 600px; line-height: 1.7; }}
        .gauge-container {{ display: flex; justify-content: center; margin: 60px 0; }}
        .gauge {{ width: 280px; text-align: center; }}
        .gauge-value {{ font-size: 96px; font-weight: 700; color: var(--accent); font-family: monospace; }}
        .gauge-label {{ font-size: 18px; color: var(--text); margin-top: 8px; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 600; }}
        .gauge-condition {{ font-size: 14px; color: var(--text-secondary); margin-top: 4px; }}
        .gauge-bar {{ height: 12px; background: var(--surface); border-radius: 6px; margin-top: 32px; overflow: hidden; border: 1px solid var(--border); }}
        .gauge-fill {{ height: 100%; width: {score}%; background: linear-gradient(90deg, var(--danger), var(--accent), var(--success)); border-radius: 6px; transition: width 0.5s; }}
        .gauge-scale {{ display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; color: var(--text-secondary); }}
        .content {{ padding: 60px 0; }}
        .section {{ margin-bottom: 48px; }}
        .section-title {{ font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .section-title::before {{ content: '//'; color: var(--accent); font-family: monospace; }}
        .data-table {{ width: 100%; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
        .data-table th, .data-table td {{ padding: 14px 16px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }}
        .data-table th {{ background: var(--surface); font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        .data-table td {{ font-family: monospace; font-size: 13px; }}
        .sources-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 24px; }}
        .source-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px; text-align: center; }}
        .source-name {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }}
        .source-value {{ font-size: 32px; font-weight: 600; color: var(--text); font-family: monospace; }}
        .source-weight {{ font-size: 11px; color: var(--accent); margin-top: 4px; }}
        .updated {{ font-size: 12px; color: var(--text-secondary); text-align: center; margin-top: 40px; }}
        footer {{ padding: 32px 0; border-top: 1px solid var(--border); text-align: center; }}
        footer p {{ font-size: 12px; color: var(--text-secondary); }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 768px) {{ .sources-grid {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 32px; }} .gauge-value {{ font-size: 64px; }} }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="breadcrumb"><a href="../website/index.html">Monarch Castle</a> / <span>CSI-008</span></div>
            <div class="status-badge"><span class="status-dot"></span><span>LIVE DATA</span></div>
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="container">
                <div class="module-id">CSI-008 // FINANCIAL INTELLIGENCE</div>
                <h1>Cloudy & Shiny Index</h1>
                <p>Unified market sentiment score aggregating fear/greed signals from stocks, crypto, and volatility indices.</p>
            </div>
        </section>
        <div class="container">
            <div class="gauge-container">
                <div class="gauge">
                    <div class="gauge-value">{score:.0f}</div>
                    <div class="gauge-label">{classification}</div>
                    <div class="gauge-condition">Condition: {condition}</div>
                    <div class="gauge-bar"><div class="gauge-fill"></div></div>
                    <div class="gauge-scale">
                        <span>0 - Fear</span>
                        <span>100 - Greed</span>
                    </div>
                </div>
            </div>
        </div>
        <section class="content">
            <div class="container">
                <div class="section">
                    <h2 class="section-title">Component Scores</h2>
                    <div class="sources-grid">
                        <div class="source-card">
                            <div class="source-name">Stock Fear/Greed</div>
                            <div class="source-value">{data["components"]["stock_fear_greed"]:.0f}</div>
                            <div class="source-weight">Weight: 40%</div>
                        </div>
                        <div class="source-card">
                            <div class="source-name">Crypto Fear/Greed</div>
                            <div class="source-value">{data["components"]["crypto_fear_greed"]}</div>
                            <div class="source-weight">Weight: 30%</div>
                        </div>
                        <div class="source-card">
                            <div class="source-name">VIX (Inverted)</div>
                            <div class="source-value">{data["components"]["vix_inverted"]:.0f}</div>
                            <div class="source-weight">Weight: 30%</div>
                        </div>
                    </div>
                </div>
                <div class="section">
                    <h2 class="section-title">Crypto Fear & Greed History (7 Days)</h2>
                    <table class="data-table">
                        <thead><tr><th>Date</th><th>Score</th><th>Classification</th></tr></thead>
                        <tbody>{crypto_history}</tbody>
                    </table>
                </div>
                <p class="updated">Last updated: {data["fetched_at"][:16].replace("T", " ")}</p>
            </div>
        </section>
    </main>
    <footer><div class="container"><p>CSI-008 · <a href="../website/index.html">Monarch Castle Technologies</a> · Data from alternative.me</p></div></footer>
</body>
</html>'''
    
    output_path = ROOT_DIR / "Cloudy&Shiny Index (Global Fear & Greed)" / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Generated {output_path}")


def build_nato_chart(countries):
    """Generate SVG bar chart for NATO spending % GDP"""
    width = 800
    height = 400
    padding_left = 120
    padding_bottom = 40
    padding_top = 40
    padding_right = 40
    
    # Sort by % GDP desc
    sorted_data = sorted(countries, key=lambda x: x['pct_gdp'], reverse=True)
    max_val = max([x['pct_gdp'] for x in sorted_data] + [4.0])
    
    bar_height = (height - padding_top - padding_bottom) / len(sorted_data)
    bar_gap = 4
    actual_bar_height = bar_height - bar_gap
    
    target_x = padding_left + (2.0 / max_val) * (width - padding_left - padding_right)
    
    bars = ""
    labels = ""
    values = ""
    
    for i, c in enumerate(sorted_data):
        y = padding_top + i * bar_height
        bar_width = (c['pct_gdp'] / max_val) * (width - padding_left - padding_right)
        
        color = "#10b981" if c['pct_gdp'] >= 2.0 else "#ef4444"
        if c['pct_gdp'] < 2.0 and c['pct_gdp'] > 1.8: color = "#f59e0b" # Near miss
        
        bars += f'<rect x="{padding_left}" y="{y}" width="{bar_width}" height="{actual_bar_height}" fill="{color}" rx="2" />'
        labels += f'<text x="{padding_left - 10}" y="{y + actual_bar_height/1.5}" text-anchor="end" fill="#9aa4b2" font-size="11">{c["flag"]} {c["name"]}</text>'
        values += f'<text x="{padding_left + bar_width + 8}" y="{y + actual_bar_height/1.5}" fill="#f5f7fa" font-size="10" font-family="monospace">{c["pct_gdp"]:.2f}%</text>'

    svg = f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="NATO spending chart">
        <rect x="0" y="0" width="{width}" height="{height}" fill="#141a24" rx="8" />
        <line x1="{target_x}" y1="{padding_top}" x2="{target_x}" y2="{height - padding_bottom}" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4 4" />
        <text x="{target_x}" y="{padding_top - 10}" text-anchor="middle" fill="#3b82f6" font-size="12" font-weight="600">2% TARGET</text>
        {bars}
        {labels}
        {values}
    </svg>
    """
    return svg


def generate_nato_page():
    """Generate NATO spending page with high-fidelity UI"""
    data = load_json("nato_spending.json")
    
    if not data:
        print("[ERROR] No NATO data found")
        return
    
    # Sort for table
    sorted_countries = sorted(data["countries"], key=lambda x: x['spending_bn'], reverse=True)
    
    # Generate country rows
    country_rows = ""
    for c in sorted_countries:
        status_class = "yes" if c["meets_target"] else "no"
        status_text = "COMPLIANT" if c["meets_target"] else "DEFICIT"
        p_capita = (c['spending_bn'] * 1e9) / (c.get('population', 1) or 1) # simple calc
        
        # Calculate deficit/surplus
        target_amount = (c['spending_bn'] / c['pct_gdp']) * 2.0
        diff = c['spending_bn'] - target_amount
        diff_str = f"+${diff:.1f}B" if diff > 0 else f"-${abs(diff):.1f}B"
        diff_class = "success" if diff > 0 else "danger"
        
        bar_width = min(100, (c['pct_gdp'] / 4.0) * 100)
        
        country_rows += f'''<tr>
            <td style="font-weight: 500; color: #fff;">{c["flag"]} {c["name"]}</td>
            <td style="font-family: monospace; color: #e3b341;">${c["spending_bn"]:.1f}B</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 60px; height: 6px; background: #1f2430; border-radius: 3px; overflow: hidden;">
                        <div style="width: {bar_width}%; height: 100%; background: {'#22c55e' if c['meets_target'] else '#ef4444'};"></div>
                    </div>
                    <span style="font-family: monospace;">{c["pct_gdp"]:.2f}%</span>
                </div>
            </td>
            <td style="font-family: monospace;" class="text-{diff_class}">{diff_str}</td>
            <td><span class="status-pill {status_class}">{status_text}</span></td>
        </tr>'''

    chart_svg = build_nato_chart(data["countries"])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NATO-005 | Alliance Expenditure Tracker</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ 
            --bg: #050608;
            --surface: #10141c;
            --panel: #141a24;
            --border: #1f2430;
            --text: #f5f7fa;
            --muted: #9aa4b2;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.4);
            --success: #22c55e;
            --danger: #ef4444;
            --warning: #f59e0b;
        }}
        body {{ 
            font-family: 'Inter', -apple-system, sans-serif; 
            background: linear-gradient(135deg, #050608 0%, #0b0f18 100%);
            color: var(--text); 
            min-height: 100vh; 
        }}
        .grid-overlay {{
            position: fixed; inset: 0; pointer-events: none; opacity: 0.4;
            background-size: 40px 40px;
            background-image: linear-gradient(to right, rgba(255,255,255,0.02) 1px, transparent 1px),
                              linear-gradient(to bottom, rgba(255,255,255,0.02) 1px, transparent 1px);
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 32px; }}
        
        /* Header */
        header {{ 
            position: sticky; top: 0; z-index: 50; 
            background: rgba(5,6,8,0.9); backdrop-filter: blur(12px); 
            border-bottom: 1px solid var(--border); 
        }}
        header .container {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 0; }}
        .brand {{ display: flex; align-items: center; gap: 12px; font-weight: 600; }}
        .brand img {{ width: 24px; height: 24px; }}
        .badge {{ 
            padding: 4px 10px; border-radius: 99px; font-size: 11px; 
            letter-spacing: 0.1em; text-transform: uppercase; border: 1px solid var(--accent); color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
        }}

        /* Hero */
        .hero {{ padding: 60px 0 40px; }}
        .module-id {{ color: var(--accent); font-family: monospace; font-size: 12px; margin-bottom: 12px; display: block; }}
        h1 {{ font-size: 48px; letter-spacing: -0.02em; font-weight: 700; background: linear-gradient(to right, #fff, #9aa4b2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }}
        .subtitle {{ color: var(--muted); font-size: 18px; max-width: 600px; line-height: 1.6; }}

        /* Stats Grid */
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 40px 0; }}
        .stat-card {{ background: var(--panel); border: 1px solid var(--border); padding: 20px; border-radius: 12px; }}
        .stat-label {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }}
        .stat-value {{ font-size: 32px; font-weight: 600; font-family: monospace; color: #fff; }}
        .stat-sub {{ font-size: 12px; color: var(--success); margin-top: 4px; }}

        /* Main Content */
        .layout-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 32px; margin-bottom: 60px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 24px; overflow: hidden; }}
        .section-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }}
        .section-title {{ font-size: 14px; font-weight: 600; text-transform: uppercase; color: var(--muted); letter-spacing: 0.1em; }}
        
        /* Table */
        .table-container {{ overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; color: var(--muted); font-size: 11px; text-transform: uppercase; padding: 12px; border-bottom: 1px solid var(--border); }}
        td {{ padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; color: var(--muted); }}
        tr:last-child td {{ border-bottom: none; }}
        
        /* Components */
        .status-pill {{ padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; }}
        .status-pill.yes {{ background: rgba(34, 197, 94, 0.1); color: var(--success); border: 1px solid rgba(34, 197, 94, 0.2); }}
        .status-pill.no {{ background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.2); }}
        .text-success {{ color: var(--success); }}
        .text-danger {{ color: var(--danger); }}
        
        footer {{ border-top: 1px solid var(--border); padding: 40px 0; text-align: center; color: var(--muted); font-size: 12px; margin-top: 80px; }}
        
        @media (max-width: 1024px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} .layout-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="grid-overlay"></div>
    <header>
        <div class="container">
            <div class="brand">
                <img src="../website/logo.png" alt="Logo">
                <span>Monarch Castle</span>
            </div>
            <div class="badge">Valid: {data["year"]}</div>
        </div>
    </header>
    
    <main class="container">
        <section class="hero">
            <span class="module-id">NATO-005 // INTELLIGENCE</span>
            <h1>NATO Expenditure Tracker</h1>
            <p class="subtitle">Strategic monitoring of North Atlantic Treaty Organization defense spending against the 2% GDP treaty obligation.</p>
        </section>

        <section class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Spending</div>
                <div class="stat-value" style="color: #e3b341">${data["summary"]["total_spending_bn"]:.0f}B</div>
                <div class="stat-sub">USD Equivalent</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Compliance Rate</div>
                <div class="stat-value">{data["summary"]["countries_meeting_target"]} <span style="font-size: 16px; color: var(--muted);">/ 31</span></div>
                <div class="stat-sub">Member States</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Burden</div>
                <div class="stat-value">{data["summary"]["avg_pct_gdp"]:.2f}%</div>
                <div class="stat-sub">of GDP</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">US Contribution</div>
                <div class="stat-value">66%</div>
                <div class="stat-sub">of Total</div>
            </div>
        </section>

        <div class="layout-grid">
            <!-- Left Column: Visuals -->
            <div style="display: flex; flex-direction: column; gap: 32px;">
                <div class="card">
                    <div class="section-header">
                        <div class="section-title">Compliance Landscape</div>
                    </div>
                    {chart_svg}
                </div>
                
                <div class="card">
                    <div class="section-header">
                        <div class="section-title">Strategic Assessment</div>
                    </div>
                    <div style="color: var(--muted); line-height: 1.6; font-size: 14px;">
                        <p style="margin-bottom: 12px;"><strong style="color: #fff;">EXECUTIVE SUMMARY:</strong> The Alliance shows a bifurcated spending pattern. While the Eastern Flank (Poland, Baltics) has rapidly accelerated spending exceeding 2.5% of GDP in response to regional threats, major Western European economies remain below the threshold.</p>
                        <p>Total capability gaps estimated at $80B+ annually to meet full spectrum dominance requirements. Recommend focused diplomatic pressure on Tier 2 economies to bridge the deficit gap.</p>
                    </div>
                </div>
            </div>

            <!-- Right Column: Data Table -->
            <div class="card">
                <div class="section-header">
                    <div class="section-title">Member Ledger</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Member</th>
                                <th>Spend</th>
                                <th>% GDP</th>
                                <th>Delta</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {country_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        NATO-005 · Monarch Castle Technologies · Source: {data["source"]}
    </footer>
</body>
</html>'''
    
    output_path = ROOT_DIR / "NATO Expenditure Tracker" / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Generated {output_path}")



def generate_oil_page():
    """Generate Oil Price page with real data"""
    data = load_json("oil_prices.json")
    
    if not data:
        print("[ERROR] No oil data found")
        return
    
    price = data["current"]["price"]
    change = data["current"]["change_1m_pct"]
    trend = "↑" if change > 0 else "↓"
    trend_color = "#10b981" if change > 0 else "#ef4444"
    
    # Generate history rows
    history_rows = ""
    for h in data["history"]:
        history_rows += f'<tr><td>{h["date"]}</td><td>${h["close"]:.2f}</td></tr>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OPI-006 | Oil Price Oracle</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0a0a0a; --surface: #141414; --border: #262626; --text: #fafafa; --text-secondary: #737373; --accent: #8b5cf6; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}
        header {{ padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(10,10,10,0.9); backdrop-filter: blur(12px); z-index: 100; }}
        header .container {{ display: flex; justify-content: space-between; align-items: center; }}
        .breadcrumb {{ display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }}
        .breadcrumb a {{ color: var(--text-secondary); text-decoration: none; }}
        .status-badge {{ display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.2); border-radius: 6px; font-size: 12px; font-weight: 500; color: var(--accent); }}
        .status-dot {{ width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: blink 2s ease-in-out infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        .hero {{ padding: 80px 0 60px; border-bottom: 1px solid var(--border); }}
        .module-id {{ font-size: 12px; font-weight: 600; color: var(--accent); letter-spacing: 0.1em; margin-bottom: 16px; font-family: monospace; }}
        .hero h1 {{ font-size: 42px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 16px; }}
        .hero p {{ font-size: 18px; color: var(--text-secondary); max-width: 600px; line-height: 1.7; }}
        .price-display {{ text-align: center; padding: 60px 0; }}
        .price-value {{ font-size: 72px; font-weight: 700; font-family: monospace; }}
        .price-change {{ font-size: 24px; margin-top: 8px; }}
        .price-label {{ font-size: 14px; color: var(--text-secondary); margin-top: 8px; }}
        .content {{ padding: 60px 0; }}
        .section {{ margin-bottom: 48px; }}
        .section-title {{ font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .section-title::before {{ content: '//'; color: var(--accent); font-family: monospace; }}
        .data-table {{ width: 100%; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
        .data-table th, .data-table td {{ padding: 14px 16px; text-align: left; font-size: 13px; border-bottom: 1px solid var(--border); }}
        .data-table th {{ background: var(--surface); font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; }}
        .data-table tr:last-child td {{ border-bottom: none; }}
        .data-table td {{ font-family: monospace; font-size: 13px; }}
        footer {{ padding: 32px 0; border-top: 1px solid var(--border); text-align: center; }}
        footer p {{ font-size: 12px; color: var(--text-secondary); }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 768px) {{ .hero h1 {{ font-size: 32px; }} .price-value {{ font-size: 48px; }} }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="breadcrumb"><a href="../website/index.html">Monarch Castle</a> / <span>OPI-006</span></div>
            <div class="status-badge"><span class="status-dot"></span><span>TRACKING</span></div>
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="container">
                <div class="module-id">OPI-006 // FINANCIAL INTELLIGENCE</div>
                <h1>Oil Price Oracle</h1>
                <p>Brent Crude oil price tracking and trend analysis.</p>
            </div>
        </section>
        <div class="container">
            <div class="price-display">
                <div class="price-value">${price:.2f}</div>
                <div class="price-change" style="color: {trend_color}">{trend} {abs(change):.1f}% (30d)</div>
                <div class="price-label">Brent Crude Futures (BZ=F)</div>
            </div>
        </div>
        <section class="content">
            <div class="container">
                <div class="section">
                    <h2 class="section-title">Price History</h2>
                    <table class="data-table">
                        <thead><tr><th>Date</th><th>Close</th></tr></thead>
                        <tbody>{history_rows}</tbody>
                    </table>
                </div>
            </div>
        </section>
    </main>
    <footer><div class="container"><p>OPI-006 · <a href="../website/index.html">Monarch Castle Technologies</a> · {data["source"]}</p></div></footer>
</body>
</html>'''
    
    output_path = ROOT_DIR / "Oil Price Prediction Intelligence" / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Generated {output_path}")


def generate_baltic_page():
    """Generate Baltic Dry Index page with real data"""
    data = load_json("baltic_dry.json")
    
    if not data:
        print("[ERROR] No Baltic Dry data found")
        return
    
    price = data["current"]["price"]
    change = data["current"]["change_3m_pct"]
    signal = data["current"]["signal"]
    trend_color = "#10b981" if change > 0 else "#ef4444"
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDI-007 | Baltic Dry Predictor</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{ --bg: #0a0a0a; --surface: #141414; --border: #262626; --text: #fafafa; --text-secondary: #737373; --accent: #06b6d4; --danger: #ef4444; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; -webkit-font-smoothing: antialiased; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 0 24px; }}
        header {{ padding: 20px 0; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(10,10,10,0.9); backdrop-filter: blur(12px); z-index: 100; }}
        header .container {{ display: flex; justify-content: space-between; align-items: center; }}
        .breadcrumb {{ display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }}
        .breadcrumb a {{ color: var(--text-secondary); text-decoration: none; }}
        .status-badge {{ display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); border-radius: 6px; font-size: 12px; font-weight: 500; color: var(--danger); }}
        .status-dot {{ width: 6px; height: 6px; background: var(--danger); border-radius: 50%; animation: blink 2s ease-in-out infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        .hero {{ padding: 80px 0 60px; border-bottom: 1px solid var(--border); }}
        .module-id {{ font-size: 12px; font-weight: 600; color: var(--accent); letter-spacing: 0.1em; margin-bottom: 16px; font-family: monospace; }}
        .hero h1 {{ font-size: 42px; font-weight: 600; letter-spacing: -0.02em; margin-bottom: 16px; }}
        .hero p {{ font-size: 18px; color: var(--text-secondary); max-width: 600px; line-height: 1.7; }}
        .signal-box {{ background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; padding: 24px; text-align: center; margin: 40px 0; }}
        .signal-title {{ font-size: 12px; color: var(--danger); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }}
        .signal-value {{ font-size: 24px; font-weight: 600; }}
        .price-display {{ text-align: center; padding: 40px 0; }}
        .price-value {{ font-size: 56px; font-weight: 700; font-family: monospace; }}
        .price-change {{ font-size: 20px; margin-top: 8px; }}
        .content {{ padding: 60px 0; }}
        .section {{ margin-bottom: 48px; }}
        .section-title {{ font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .section-title::before {{ content: '//'; color: var(--accent); font-family: monospace; }}
        .section p {{ font-size: 15px; color: var(--text-secondary); line-height: 1.8; }}
        .theory-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 24px; margin-top: 16px; }}
        .theory-box h4 {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--accent); }}
        .theory-box p {{ font-size: 14px; color: var(--text-secondary); line-height: 1.7; }}
        footer {{ padding: 32px 0; border-top: 1px solid var(--border); text-align: center; }}
        footer p {{ font-size: 12px; color: var(--text-secondary); }}
        footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 768px) {{ .hero h1 {{ font-size: 32px; }} .price-value {{ font-size: 40px; }} }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="breadcrumb"><a href="../website/index.html">Monarch Castle</a> / <span>BDI-007</span></div>
            <div class="status-badge"><span class="status-dot"></span><span>WARNING</span></div>
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="container">
                <div class="module-id">BDI-007 // FINANCIAL INTELLIGENCE</div>
                <h1>Baltic Dry-Growth Prediction</h1>
                <p>Correlate the Baltic Dry Index with global economic indicators. A leading predictor of economic health.</p>
            </div>
        </section>
        <div class="container">
            <div class="signal-box">
                <div class="signal-title">Economic Signal</div>
                <div class="signal-value">{signal}</div>
            </div>
            <div class="price-display">
                <div class="price-value">${price:.2f}</div>
                <div class="price-change" style="color: {trend_color}">{change:+.1f}% (3 months)</div>
            </div>
        </div>
        <section class="content">
            <div class="container">
                <div class="section">
                    <h2 class="section-title">Analysis</h2>
                    <div class="theory-box">
                        <h4>Leading Indicator Interpretation</h4>
                        <p>{data["analysis"]["interpretation"]}</p>
                    </div>
                </div>
            </div>
        </section>
    </main>
    <footer><div class="container"><p>BDI-007 · <a href="../website/index.html">Monarch Castle Technologies</a> · {data["source"]}</p></div></footer>
</body>
</html>'''
    
    output_path = ROOT_DIR / "Baltic Dry-Growth Prediction" / "index.html"      
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Generated {output_path}")


def srti_safe_text(value):
    return html_lib.escape(str(value or ""), quote=True)


def srti_safe_url(value):
    candidate = str(value or "").strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return html_lib.escape(candidate, quote=True)


def srti_parse_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def srti_format_time(value):
    parsed = srti_parse_time(value)
    return parsed.strftime("%Y-%m-%d %H:%M UTC") if parsed else "Unavailable"


def srti_region_label(region):
    labels = {
        "mali": "Mali",
        "niger": "Niger",
        "burkina_faso": "Burkina Faso",
        "sahel": "Sahel",
    }
    return labels.get(region, str(region).replace("_", " ").title())


def build_srti_operator_chart(history):
    points = history[-48:]
    scores = [max(0.0, min(100.0, float(item.get("score", 0)))) for item in points]
    if not scores:
        scores = [0.0]
    width, height = 860, 250
    left, right, top, bottom = 42, 18, 18, 34
    plot_width = width - left - right
    plot_height = height - top - bottom
    denominator = max(1, len(scores) - 1)

    coordinates = []
    for index, score in enumerate(scores):
        x_value = left + (index * plot_width / denominator)
        y_value = top + ((100 - score) * plot_height / 100)
        coordinates.append(f"{x_value:.1f},{y_value:.1f}")

    grid = []
    for value in range(0, 101, 20):
        y_value = top + ((100 - value) * plot_height / 100)
        grid.append(
            f'<line x1="{left}" y1="{y_value:.1f}" x2="{width - right}" '
            f'y2="{y_value:.1f}" stroke="#26303d" stroke-width="1" />'
            f'<text x="{left - 8}" y="{y_value + 4:.1f}" text-anchor="end" '
            f'fill="#95a1af" font-size="10">{value}</text>'
        )

    start = srti_format_time(points[0].get("timestamp")) if points else ""
    end = srti_format_time(points[-1].get("timestamp")) if points else ""
    return f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="trend-title trend-desc">
        <title id="trend-title">Accepted SRTI snapshot history</title>
        <desc id="trend-desc">Fixed zero to one hundred scale, from {srti_safe_text(start)} to {srti_safe_text(end)}.</desc>
        {''.join(grid)}
        <polyline points="{' '.join(coordinates)}" fill="none" stroke="#66d9e8" stroke-width="2.5" vector-effect="non-scaling-stroke" />
        <circle cx="{coordinates[-1].split(',')[0]}" cy="{coordinates[-1].split(',')[1]}" r="4" fill="#d4af37" />
        <text x="{left}" y="{height - 9}" fill="#95a1af" font-size="10">{srti_safe_text(start)}</text>
        <text x="{width - right}" y="{height - 9}" text-anchor="end" fill="#95a1af" font-size="10">{srti_safe_text(end)}</text>
    </svg>
    """


def render_srti_operator_html(latest, history, asset_prefix, data_prefix):
    risk = str(latest.get("risk_level", "UNKNOWN")).upper()
    risk_class = f"risk-{risk.lower()}"
    score = max(0.0, min(100.0, float(latest.get("score", 0))))
    window_hours = int(latest.get("window_hours", 72))
    fetched_at = str(latest.get("fetched_at") or "")
    content_at = latest.get("content_latest_at") or fetched_at
    sources = latest.get("sources") or []
    reachable = [source for source in sources if source.get("status") == "ok"]
    gate = latest.get("quality_gate") or {}
    criteria = gate.get("criteria") or {}
    gate_label = "GATE PASSED" if gate.get("passed") else "LEGACY SNAPSHOT"
    previous_score = score
    if len(history) > 1:
        previous_score = float(history[-2].get("score", score))
    delta = score - previous_score
    delta_label = f"{delta:+.1f} vs previous accepted run"

    component_rows = []
    for key, value in (latest.get("components") or {}).items():
        numeric_value = max(0.0, min(100.0, float(value)))
        weight = float((latest.get("weights") or {}).get(key, 0)) * 100
        component_rows.append(f"""
        <div class="component">
            <div class="component-top">
                <span class="component-name">{srti_safe_text(key.replace('_', ' '))}</span>
                <span class="component-value">{numeric_value:.1f}</span>
            </div>
            <progress class="component-progress" max="100" value="{numeric_value:.1f}">{numeric_value:.1f}</progress>
            <div class="component-meta">Normalized component · {weight:.1f}% composite weight</div>
        </div>
        """)
    if not component_rows:
        component_rows.append('<div class="empty-state">No component detail in this snapshot.</div>')

    event_rows = []
    for item in (latest.get("top_headlines") or [])[:8]:
        title = srti_safe_text(item.get("title") or "Untitled source item")
        link = srti_safe_url(item.get("link"))
        title_markup = (
            f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>'
            if link
            else title
        )
        regions = sorted(set(item.get("regions") or []))
        region_tokens = " ".join(srti_safe_text(region) for region in regions)
        tags = [
            f'<span class="tag">{srti_safe_text(srti_region_label(region))}</span>'
            for region in regions
        ]
        tags.extend(
            f'<span class="tag">{srti_safe_text(str(tag).replace("_", " "))}</span>'
            for tag in (item.get("tags") or [])
        )
        item_score = float(item.get("score", 0))
        event_rows.append(f"""
        <article class="event" data-regions="{region_tokens}">
            <div>
                <h3 class="event-title">{title_markup}</h3>
                <div class="event-meta">{srti_safe_text(item.get('source'))} · {srti_safe_text(srti_format_time(item.get('published_at')))}</div>
                <div class="tags">{''.join(tags)}</div>
            </div>
            <div class="event-score">{item_score:.2f}<span>ITEM WEIGHT</span></div>
        </article>
        """)
    if not event_rows:
        event_rows.append('<div class="empty-state">No risk-keyword items passed this accepted collection window.</div>')

    status_labels = {"ok": "reachable", "empty": "no items", "unreachable": "unreachable"}
    source_rows = []
    for source in sources:
        source_url = srti_safe_url(source.get("url"))
        name = srti_safe_text(source.get("name"))
        name_markup = (
            f'<a href="{source_url}" target="_blank" rel="noopener noreferrer">{name}</a>'
            if source_url
            else name
        )
        source_state = str(source.get("status") or "unknown")
        source_rows.append(f"""
        <tr>
            <td>{name_markup}</td>
            <td><span class="source-state {srti_safe_text(source_state)}">{srti_safe_text(status_labels.get(source_state, source_state))}</span></td>
            <td>{int(source.get('items') or 0)} fetched / {int(source.get('eligible_items') or 0)} dated</td>
        </tr>
        """)

    covered_regions = [srti_region_label(region) for region in gate.get("covered_regions", [])]
    coverage_text = ", ".join(covered_regions) if covered_regions else "Not recorded"
    history_methods = {
        str(item.get("methodology_version") or "legacy") for item in history[-48:]
    }
    trend_method_label = (
        "MIXED METHODS · FIXED AXIS"
        if len(history_methods) > 1
        else f"METHOD {next(iter(history_methods), 'unknown')} · FIXED AXIS"
    )
    trend_chart = build_srti_operator_chart(history)
    methodology_version = srti_safe_text(latest.get("methodology_version") or "legacy")
    schema_version = srti_safe_text(latest.get("schema_version") or "legacy")
    evaluated = int(latest.get("items_evaluated") or latest.get("items_count") or 0)
    signalled = int(latest.get("items_count") or 0)
    asset_prefix = asset_prefix.rstrip("/")
    data_prefix = data_prefix.rstrip("/")

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="SRTI is a transparent, deterministic monitor of public Sahel security reporting for Mali, Niger, and Burkina Faso.">
    <meta name="theme-color" content="#07090c">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
    <title>SRTI | Sahel Region Threat Index</title>
    <link rel="icon" type="image/png" href="{asset_prefix}/mc-mark.png">
    <link rel="stylesheet" href="{asset_prefix}/srti.css?v=2.0">
    <script src="{asset_prefix}/srti.js?v=2.0" defer></script>
</head>
<body class="{srti_safe_text(risk_class)}">
    <header class="topbar">
        <div class="topbar-inner">
            <div class="brand">
                <img src="{asset_prefix}/mc-mark.png" alt="Monarch Castle Technologies mark" width="34" height="34">
                <div>
                    <div class="brand-name">Monarch Castle Technologies</div>
                    <div class="brand-product">SRTI / PUBLIC OSINT MONITOR</div>
                </div>
            </div>
            <div class="snapshot-state" data-collected-at="{srti_safe_text(fetched_at)}" data-state="recent">
                <span class="snapshot-dot" aria-hidden="true"></span>
                <span data-snapshot-label>SNAPSHOT · {srti_safe_text(srti_format_time(fetched_at))}</span>
            </div>
        </div>
    </header>

    <main class="shell">
        <section class="command-head">
            <div>
                <div class="eyebrow">SRTI-004 / SAHEL REGION THREAT INDEX</div>
                <h1>Regional signal picture. Sources exposed.</h1>
                <p class="lede">Deterministic monitoring of public reporting about Mali, Niger, and Burkina Faso. Use the score to triage evidence—not as an incident count, probability, or verified intelligence assessment.</p>
            </div>
            <div class="scope-panel">
                <strong>COLLECTION SCOPE / {window_hours}H</strong>
                <p>Public RSS and public HTML fallback. No API account, private feed, model classification, or operator login.</p>
            </div>
        </section>

        <section class="status-strip" aria-label="Snapshot status">
            <div class="status-cell">
                <div class="metric-label">Collection attempt</div>
                <div class="status-value">{srti_safe_text(srti_format_time(fetched_at))}</div>
                <div class="status-sub">Publication timestamp, not continuous monitoring</div>
            </div>
            <div class="status-cell">
                <div class="metric-label">Newest evaluated item</div>
                <div class="status-value">{srti_safe_text(srti_format_time(content_at))}</div>
                <div class="status-sub">Publisher timestamp where available</div>
            </div>
            <div class="status-cell">
                <div class="metric-label">Source response</div>
                <div class="status-value">{len(reachable)} / {len(sources)}</div>
                <div class="status-sub">Last accepted collection attempt</div>
            </div>
            <div class="status-cell">
                <div class="metric-label">Publication gate</div>
                <div class="status-value">{srti_safe_text(gate_label)}</div>
                <div class="status-sub">Failed runs retain last-known-good data</div>
            </div>
        </section>

        <div class="workspace">
            <div class="stack">
                <section class="panel" aria-labelledby="signal-heading">
                    <div class="panel-head">
                        <h2 class="panel-title" id="signal-heading">Signal summary</h2>
                        <div class="panel-note">METHOD {methodology_version} · FIXED 0–100 SCALE</div>
                    </div>
                    <div class="score-layout">
                        <div class="score-block">
                            <div class="metric-label">Composite signal</div>
                            <div class="score-number">{score:.1f}</div>
                            <div class="score-scale">/ 100 · {srti_safe_text(delta_label)}</div>
                            <div class="risk-row">
                                <span class="status-chip">{srti_safe_text(risk)}</span>
                                <span class="risk-help">heuristic band</span>
                            </div>
                        </div>
                        <div class="component-list">{''.join(component_rows)}</div>
                    </div>
                </section>

                <section class="panel" aria-labelledby="trend-heading">
                    <div class="panel-head">
                        <h2 class="panel-title" id="trend-heading">Accepted snapshot trend</h2>
                        <div class="panel-note">LAST {min(48, len(history))} RUNS · {srti_safe_text(trend_method_label)}</div>
                    </div>
                    <div class="trend-wrap">{trend_chart}</div>
                </section>

                <section class="panel" aria-labelledby="queue-heading">
                    <div class="panel-head">
                        <h2 class="panel-title" id="queue-heading">Evidence queue</h2>
                        <div class="filters" aria-label="Filter evidence by region">
                            <button class="filter" type="button" data-filter="all" aria-pressed="true">All</button>
                            <button class="filter" type="button" data-filter="mali" aria-pressed="false">Mali</button>
                            <button class="filter" type="button" data-filter="niger" aria-pressed="false">Niger</button>
                            <button class="filter" type="button" data-filter="burkina_faso" aria-pressed="false">Burkina Faso</button>
                        </div>
                    </div>
                    <div class="event-list">{''.join(event_rows)}</div>
                    <div class="empty-state" data-filter-empty hidden>No evidence items match this region in the current snapshot.</div>
                </section>

                <section class="panel" aria-labelledby="sources-heading">
                    <div class="panel-head">
                        <h2 class="panel-title" id="sources-heading">Source ledger</h2>
                        <div class="panel-note">STATUS FROM LAST ATTEMPT · LINKS OPEN PUBLISHERS</div>
                    </div>
                    <table class="source-table">
                        <thead><tr><th class="table-label">Source</th><th class="table-label">Response</th><th class="table-label">Items</th></tr></thead>
                        <tbody>{''.join(source_rows)}</tbody>
                    </table>
                </section>
            </div>

            <aside class="stack" aria-label="Method and provenance">
                <section class="panel">
                    <div class="panel-head">
                        <h2 class="panel-title">Operator context</h2>
                        <div class="panel-note">{signalled} SIGNALLED / {evaluated} EVALUATED</div>
                    </div>
                    <div class="method-grid">
                        <div class="method-card">
                            <div class="section-kicker">01 / SCOPE</div>
                            <h3>Three-country watch</h3>
                            <p>Mali, Niger, Burkina Faso, plus explicitly Sahel-wide reporting.</p>
                        </div>
                        <div class="method-card">
                            <div class="section-kicker">02 / INPUT</div>
                            <h3>Publisher timestamps</h3>
                            <p>Undated and out-of-window items are excluded from scoring.</p>
                        </div>
                        <div class="method-card">
                            <div class="section-kicker">03 / MODEL</div>
                            <h3>Deterministic heuristic</h3>
                            <p>Complete-term keyword hits, source weight, and recency decay. No generative model.</p>
                        </div>
                        <div class="method-card">
                            <div class="section-kicker">04 / LIMIT</div>
                            <h3>Not independently verified</h3>
                            <p>Feeds can lag, duplicate, mistranslate, or omit events. Open source before acting.</p>
                        </div>
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-head">
                        <h2 class="panel-title">Quality gate</h2>
                        <div class="panel-note">{srti_safe_text(gate_label)}</div>
                    </div>
                    <ul class="gate-list">
                        <li>{len(reachable)} responding sources; minimum {int(criteria.get('minimum_reachable_sources') or 0)}.</li>
                        <li>Target-country coverage: {srti_safe_text(coverage_text)}; minimum {int(criteria.get('minimum_target_countries') or 0)} countries.</li>
                        <li>{int(gate.get('dated_items') or 0)} dated items; minimum {int(criteria.get('minimum_dated_items') or 0)}.</li>
                        <li>On gate failure, no snapshot, history, event log, or site publication is replaced.</li>
                    </ul>
                </section>

                <section class="panel">
                    <div class="panel-head">
                        <h2 class="panel-title">Machine-readable evidence</h2>
                        <div class="panel-note">SCHEMA {schema_version}</div>
                    </div>
                    <div class="download-row">
                        <a class="download-link" href="{data_prefix}/srti_latest.json">CURRENT ACCEPTED SNAPSHOT <span>JSON ↗</span></a>
                        <a class="download-link" href="{data_prefix}/srti_history.json">ACCEPTED HISTORY <span>JSON ↗</span></a>
                    </div>
                </section>
            </aside>
        </div>
    </main>

    <footer class="shell">
        <span>SRTI-004 · Monarch Castle Technologies · Informational open-source monitor.</span>
        <span>Not military advice · Verify linked reporting before use.</span>
    </footer>
</body>
</html>
"""


def generate_srti_page():
    """Generate SRTI page with OSINT RSS data."""
    latest = load_json("srti_latest.json")
    history = load_json("srti_history.json")

    if not latest or not history:
        print("[ERROR] No SRTI data found")
        return

    module_html = render_srti_operator_html(latest, history, "../assets", "../data")
    output_path = ROOT_DIR / "Sahel Region Threat Index (SRTI)" / "index.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(module_html)
    print(f"[OK] Generated {output_path}")

    root_html = render_srti_operator_html(latest, history, "assets", "data")
    root_path = ROOT_DIR / "index.html"
    with open(root_path, 'w', encoding='utf-8') as f:
        f.write(root_html)
    print(f"[OK] Generated {root_path}")


def main():
    print("=" * 50)
    print("MONARCH CASTLE - STATIC PAGE GENERATOR")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 50)

    print("\n[1/5] Generating Sentiment Index page...")
    generate_sentiment_page()

    print("\n[2/5] Generating NATO page...")
    generate_nato_page()

    print("\n[3/5] Generating Oil Price page...")
    generate_oil_page()
    
    print("\n[4/5] Generating Baltic Dry page...")
    generate_baltic_page()

    print("\n[5/5] Generating SRTI page...")
    generate_srti_page()

    print("\n" + "=" * 50)
    print("STATIC PAGE GENERATION COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
