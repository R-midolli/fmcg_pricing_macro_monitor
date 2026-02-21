"""
Generate a standalone interactive HTML dashboard using Plotly
for embedding in the portfolio website.
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
RAW = os.path.join(DATA_DIR, "raw")
MARTS = os.path.join(DATA_DIR, "marts")


def build_portfolio_dashboard():
    """Generate a self-contained HTML dashboard for the portfolio."""

    # Load data
    commodities = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))
    fx = pd.read_parquet(os.path.join(MARTS, "fact_fx.parquet"))
    inflation = pd.read_parquet(os.path.join(MARTS, "fact_inflation.parquet"))
    pressure = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))

    # Color palette (dark theme)
    colors = {
        "Cocoa": "#f59e0b",
        "Coffee": "#ef4444",
        "Sugar": "#22c55e",
        "Wheat": "#3b82f6",
    }
    bg_color = "#0e1117"
    card_bg = "rgba(255,255,255,0.04)"
    grid_color = "rgba(255,255,255,0.06)"
    text_color = "#e0e3eb"
    muted_color = "#8b92a5"

    # ── Figure 1: Commodity Prices (line chart) ─────────────────────────
    fig1 = go.Figure()
    for commodity in ["Cocoa", "Coffee", "Sugar", "Wheat"]:
        df_c = commodities[commodities["commodity"] == commodity].sort_values("date")
        fig1.add_trace(go.Scatter(
            x=df_c["date"], y=df_c["price_usd"],
            name=commodity, mode="lines",
            line=dict(width=2.5, color=colors[commodity]),
            hovertemplate=f"<b>{commodity}</b><br>%{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>",
        ))
    fig1.update_layout(
        title=dict(text="Agricultural Commodity Prices (USD)", font=dict(size=18, color=text_color)),
        template="plotly_dark", paper_bgcolor=bg_color, plot_bgcolor=bg_color,
        xaxis=dict(gridcolor=grid_color, showline=False),
        yaxis=dict(gridcolor=grid_color, showline=False, title="Price (USD)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(color=text_color)),
        margin=dict(l=50, r=20, t=60, b=40),
        height=380,
    )

    # ── Figure 2: EUR/USD FX Rate ────────────────────────────────────────
    fx_sorted = fx.sort_values("date")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=fx_sorted["date"], y=fx_sorted["fx_eur_usd"],
        mode="lines", name="EUR/USD",
        line=dict(width=2.5, color="#818cf8"),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.08)",
        hovertemplate="<b>EUR/USD</b><br>%{x|%b %Y}<br>%{y:.4f}<extra></extra>",
    ))
    fig2.update_layout(
        title=dict(text="EUR/USD Exchange Rate", font=dict(size=18, color=text_color)),
        template="plotly_dark", paper_bgcolor=bg_color, plot_bgcolor=bg_color,
        xaxis=dict(gridcolor=grid_color, showline=False),
        yaxis=dict(gridcolor=grid_color, showline=False, title="EUR/USD"),
        margin=dict(l=50, r=20, t=60, b=40),
        height=380,
    )

    # ── Figure 3: YoY Commodity Changes (bar chart) ─────────────────────
    latest = commodities.dropna(subset=["yoy_change_pct"]).sort_values("date").groupby("commodity").last().reset_index()
    latest = latest.sort_values("yoy_change_pct", ascending=True)
    bar_colors = [colors.get(c, "#6366f1") for c in latest["commodity"]]
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=latest["yoy_change_pct"], y=latest["commodity"],
        orientation="h", marker_color=bar_colors,
        text=[f"{v:+.1f}%" for v in latest["yoy_change_pct"]],
        textposition="outside", textfont=dict(color=text_color, size=13),
        hovertemplate="<b>%{y}</b><br>YoY: %{x:+.1f}%<extra></extra>",
    ))
    fig3.update_layout(
        title=dict(text="Latest YoY Price Change by Commodity", font=dict(size=18, color=text_color)),
        template="plotly_dark", paper_bgcolor=bg_color, plot_bgcolor=bg_color,
        xaxis=dict(gridcolor=grid_color, showline=False, title="YoY Change %",
                   zeroline=True, zerolinecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor=grid_color, showline=False),
        margin=dict(l=80, r=60, t=60, b=40),
        height=340,
    )

    # ── Figure 4: France CPI Inflation by Category ──────────────────────
    inflation_latest = inflation.dropna(subset=["yoy_inflation_pct"]).sort_values("date").groupby("category").last().reset_index()
    inflation_latest = inflation_latest.sort_values("yoy_inflation_pct", ascending=True)
    cat_colors = ["#ef4444" if v > 0 else "#22c55e" for v in inflation_latest["yoy_inflation_pct"]]
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=inflation_latest["yoy_inflation_pct"], y=inflation_latest["category"],
        orientation="h", marker_color=cat_colors,
        text=[f"{v:+.1f}%" for v in inflation_latest["yoy_inflation_pct"]],
        textposition="outside", textfont=dict(color=text_color, size=12),
        hovertemplate="<b>%{y}</b><br>Inflation YoY: %{x:+.1f}%<extra></extra>",
    ))
    fig4.update_layout(
        title=dict(text="France CPI — YoY Inflation by Food Category (%)", font=dict(size=18, color=text_color)),
        template="plotly_dark", paper_bgcolor=bg_color, plot_bgcolor=bg_color,
        xaxis=dict(gridcolor=grid_color, showline=False, title="YoY Inflation %",
                   zeroline=True, zerolinecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(gridcolor=grid_color, showline=False),
        margin=dict(l=160, r=60, t=60, b=40),
        height=400,
    )

    # ── Figure 5: Cost Squeeze Heatmap ──────────────────────────────────
    squeeze_pivot = pressure.pivot_table(
        index="inflation_category", columns="commodity",
        values="cost_squeeze_score", aggfunc="mean"
    ).fillna(0)
    fig5 = go.Figure(data=go.Heatmap(
        z=squeeze_pivot.values,
        x=squeeze_pivot.columns.tolist(),
        y=squeeze_pivot.index.tolist(),
        colorscale=[[0, "#1e3a5f"], [0.3, "#22c55e"], [0.5, "#fbbf24"], [0.7, "#f97316"], [1, "#ef4444"]],
        text=[[f"{v:.1f}" for v in row] for row in squeeze_pivot.values],
        texttemplate="%{text}", textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Squeeze: %{z:.1f}<extra></extra>",
        colorbar=dict(title=dict(text="Squeeze Score", font=dict(color=text_color)),
                      tickfont=dict(color=muted_color)),
    ))
    fig5.update_layout(
        title=dict(text="Cost Squeeze Heatmap (Input Cost Rise − CPI Rise)", font=dict(size=18, color=text_color)),
        template="plotly_dark", paper_bgcolor=bg_color, plot_bgcolor=bg_color,
        xaxis=dict(title="Commodity", color=text_color),
        yaxis=dict(title="CPI Category", color=text_color),
        margin=dict(l=160, r=20, t=60, b=60),
        height=400,
    )

    # ── Assemble the full HTML ──────────────────────────────────────────
    kpi_fx = fx_sorted.iloc[-1]["fx_eur_usd"] if len(fx_sorted) > 0 else 0
    kpi_cocoa = commodities[commodities["commodity"] == "Cocoa"].sort_values("date").iloc[-1]["price_usd"] if len(commodities) > 0 else 0
    kpi_coffee = commodities[commodities["commodity"] == "Coffee"].sort_values("date").iloc[-1]["price_usd"] if len(commodities) > 0 else 0

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FMCG Cost Pressure Monitor — Dashboard</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:{bg_color};color:{text_color};font-family:'DM Sans','Segoe UI',system-ui,sans-serif;padding:24px;min-height:100vh}}
  .dash-header{{text-align:center;padding:32px 0 24px}}
  .dash-header h1{{font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#3b82f6,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
  .dash-header p{{color:{muted_color};font-size:.92rem}}
  .kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}}
  .kpi-card{{background:{card_bg};border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:20px 24px;text-align:center;transition:transform .2s,border-color .2s}}
  .kpi-card:hover{{transform:translateY(-3px);border-color:rgba(91,140,255,.3)}}
  .kpi-value{{font-size:1.8rem;font-weight:800;margin-bottom:4px}}
  .kpi-label{{font-size:.82rem;color:{muted_color};font-weight:600;text-transform:uppercase;letter-spacing:.05em}}
  .kpi-value.blue{{background:linear-gradient(135deg,#3b82f6,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .kpi-value.amber{{background:linear-gradient(135deg,#f59e0b,#fbbf24);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .kpi-value.red{{background:linear-gradient(135deg,#ef4444,#f87171);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .kpi-value.green{{background:linear-gradient(135deg,#22c55e,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .chart-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:24px;margin-bottom:24px}}
  .chart-card{{background:{card_bg};border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px;overflow:hidden}}
  .chart-full{{background:{card_bg};border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px;margin-bottom:24px;overflow:hidden}}
  .source-badge{{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:6px;background:rgba(91,140,255,.08);border:1px solid rgba(91,140,255,.2);font-size:.78rem;font-weight:600;color:#5b8cff;margin:3px}}
  .sources-bar{{text-align:center;margin-bottom:24px}}
  @media(max-width:700px){{.chart-grid{{grid-template-columns:1fr}}.kpi-row{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<div class="dash-header">
  <h1>🛒 FMCG Cost Pressure Monitor</h1>
  <p>France · Real data from ECB, INSEE, Yahoo Finance & Open Food Facts</p>
</div>
<div class="sources-bar">
  <span class="source-badge">🏦 ECB — EUR/USD</span>
  <span class="source-badge">📊 INSEE — CPI France</span>
  <span class="source-badge">📈 Yahoo Finance — Commodities</span>
  <span class="source-badge">🥫 Open Food Facts — Products</span>
</div>
<div class="kpi-row">
  <div class="kpi-card"><div class="kpi-value blue">{kpi_fx:.4f}</div><div class="kpi-label">EUR / USD</div></div>
  <div class="kpi-card"><div class="kpi-value amber">${kpi_cocoa:,.0f}</div><div class="kpi-label">Cocoa (USD/t)</div></div>
  <div class="kpi-card"><div class="kpi-value red">${kpi_coffee:,.0f}</div><div class="kpi-label">Coffee (USD/lb)</div></div>
  <div class="kpi-card"><div class="kpi-value green">4 APIs</div><div class="kpi-label">Real Data Sources</div></div>
</div>
""")

    # Add charts
    config = {"displayModeBar": False, "responsive": True}
    html_parts.append('<div class="chart-grid">')
    html_parts.append(f'<div class="chart-card">{fig1.to_html(full_html=False, include_plotlyjs="cdn", config=config)}</div>')
    html_parts.append(f'<div class="chart-card">{fig2.to_html(full_html=False, include_plotlyjs=False, config=config)}</div>')
    html_parts.append('</div>')

    html_parts.append('<div class="chart-grid">')
    html_parts.append(f'<div class="chart-card">{fig3.to_html(full_html=False, include_plotlyjs=False, config=config)}</div>')
    html_parts.append(f'<div class="chart-card">{fig4.to_html(full_html=False, include_plotlyjs=False, config=config)}</div>')
    html_parts.append('</div>')

    html_parts.append(f'<div class="chart-full">{fig5.to_html(full_html=False, include_plotlyjs=False, config=config)}</div>')

    html_parts.append("""
<script>
  // Auto-resize notification for parent iframe
  (function(){
    function send(){
      var h = document.documentElement.scrollHeight;
      if(window.parent) window.parent.postMessage({type:'rm-iframe-height',height:h},'*');
    }
    send();
    window.addEventListener('resize', send);
    setInterval(send, 2000);
  })();
</script>
</body></html>""")

    full_html = "\n".join(html_parts)

    # Save to portfolio reports folder
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "portfolio_rafael_midolli", "reports", "dashboard_fmcg.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Dashboard saved to: {os.path.abspath(output_path)}")
    print(f"Size: {len(full_html):,} bytes")

    # Also save locally for reference
    local_path = os.path.join(DATA_DIR, "dashboard_fmcg.html")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Local copy saved to: {os.path.abspath(local_path)}")


if __name__ == "__main__":
    build_portfolio_dashboard()
