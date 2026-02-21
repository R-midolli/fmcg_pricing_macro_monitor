"""
Generate a standalone interactive HTML dashboard with Plotly.js
for embedding in the portfolio website.
Includes: filters, storytelling, responsive design.
"""
import pandas as pd
import plotly.graph_objects as go
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
MARTS = os.path.join(DATA_DIR, "marts")

COLORS = {
    "Cocoa": "#f59e0b",
    "Coffee": "#ef4444",
    "Sugar": "#22c55e",
    "Wheat": "#3b82f6",
}
BG = "#0e1117"
CARD = "rgba(255,255,255,0.04)"
GRID = "rgba(255,255,255,0.06)"
TEXT = "#e0e3eb"
MUTED = "#8b92a5"
ACCENT = "#5b8cff"


def base_layout(**overrides):
    """Build a Plotly layout dict, merging overrides properly."""
    layout = dict(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans,system-ui,sans-serif", color=TEXT),
        margin=overrides.pop("margin", dict(l=50, r=20, t=50, b=40)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=TEXT)),
    )
    # Merge xaxis / yaxis defaults
    xaxis_defaults = dict(gridcolor=GRID, showline=False)
    yaxis_defaults = dict(gridcolor=GRID, showline=False)
    xaxis_over = overrides.pop("xaxis", {})
    yaxis_over = overrides.pop("yaxis", {})
    layout["xaxis"] = {**xaxis_defaults, **xaxis_over}
    layout["yaxis"] = {**yaxis_defaults, **yaxis_over}
    layout.update(overrides)
    return layout



def fig_commodities(df):
    fig = go.Figure()
    for c in ["Cocoa", "Coffee", "Sugar", "Wheat"]:
        d = df[df["commodity"] == c].sort_values("date")
        fig.add_trace(go.Scatter(
            x=d["date"], y=d["price_usd"], name=c, mode="lines",
            line=dict(width=2.5, color=COLORS[c]),
            hovertemplate=f"<b>{c}</b><br>%{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>",
        ))
    fig.update_layout(**base_layout(height=380,
                      title=dict(text="Commodity Prices (USD)", font=dict(size=16))))
    return fig


def fig_fx(df):
    d = df.sort_values("date")
    fig = go.Figure(go.Scatter(
        x=d["date"], y=d["fx_eur_usd"], mode="lines", name="EUR/USD",
        line=dict(width=2.5, color="#818cf8"),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.06)",
        hovertemplate="<b>EUR/USD</b><br>%{x|%b %Y}<br>%{y:.4f}<extra></extra>",
    ))
    fig.update_layout(**base_layout(height=380, showlegend=False,
                      title=dict(text="EUR/USD Exchange Rate", font=dict(size=16))))
    return fig


def fig_yoy_commodity(df):
    latest = df.dropna(subset=["yoy_change_pct"]).sort_values("date").groupby("commodity").last().reset_index()
    latest = latest.sort_values("yoy_change_pct", ascending=True)
    bar_colors = ["#ef4444" if v > 0 else "#22c55e" for v in latest["yoy_change_pct"]]
    fig = go.Figure(go.Bar(
        x=latest["yoy_change_pct"], y=latest["commodity"], orientation="h",
        marker_color=bar_colors,
        text=[f"{v:+.1f}%" for v in latest["yoy_change_pct"]],
        textposition="outside", textfont=dict(color=TEXT, size=13),
        hovertemplate="<b>%{y}</b><br>YoY: %{x:+.1f}%<extra></extra>",
    ))
    fig.update_layout(**base_layout(height=320, showlegend=False,
                      title=dict(text="YoY Price Change (%)", font=dict(size=16)),
                      xaxis=dict(zeroline=True, zerolinecolor="rgba(255,255,255,0.15)")))
    return fig


def fig_inflation(df):
    latest = df.dropna(subset=["yoy_inflation_pct"]).sort_values("date").groupby("category").last().reset_index()
    latest = latest.sort_values("yoy_inflation_pct", ascending=True)
    bar_colors = ["#ef4444" if v > 0 else "#22c55e" for v in latest["yoy_inflation_pct"]]
    fig = go.Figure(go.Bar(
        x=latest["yoy_inflation_pct"], y=latest["category"], orientation="h",
        marker_color=bar_colors,
        text=[f"{v:+.1f}%" for v in latest["yoy_inflation_pct"]],
        textposition="outside", textfont=dict(color=TEXT, size=12),
        hovertemplate="<b>%{y}</b><br>YoY: %{x:+.1f}%<extra></extra>",
    ))
    fig.update_layout(**base_layout(height=380, showlegend=False,
                      title=dict(text="France CPI — YoY Inflation by Food Category", font=dict(size=16)),
                      xaxis=dict(zeroline=True, zerolinecolor="rgba(255,255,255,0.15)"),
                      margin=dict(l=160, r=60, t=50, b=40)))
    return fig


def fig_squeeze(df):
    pivot = df.pivot_table(index="inflation_category", columns="commodity",
                           values="cost_squeeze_score", aggfunc="mean").fillna(0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, "#1e3a5f"], [0.3, "#22c55e"], [0.5, "#fbbf24"], [0.7, "#f97316"], [1, "#ef4444"]],
        text=[[f"{v:.1f}" for v in row] for row in pivot.values],
        texttemplate="%{text}", textfont=dict(size=13, color="white"),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Squeeze: %{z:.1f}<extra></extra>",
        colorbar=dict(title=dict(text="Score", font=dict(color=TEXT)), tickfont=dict(color=MUTED)),
    ))
    fig.update_layout(**base_layout(height=380,
                      title=dict(text="Cost Squeeze Matrix", font=dict(size=16)),
                      xaxis=dict(title="", color=TEXT), yaxis=dict(title="", color=TEXT),
                      margin=dict(l=160, r=20, t=50, b=40)))
    return fig


def build_portfolio_dashboard():
    commodities = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))
    fx = pd.read_parquet(os.path.join(MARTS, "fact_fx.parquet"))
    inflation = pd.read_parquet(os.path.join(MARTS, "fact_inflation.parquet"))
    pressure = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))

    # KPIs
    fx_sorted = fx.sort_values("date")
    kpi_fx = fx_sorted.iloc[-1]["fx_eur_usd"] if len(fx_sorted) > 0 else 0
    kpi_cocoa = commodities[commodities["commodity"]=="Cocoa"].sort_values("date").iloc[-1]["price_usd"]
    kpi_coffee = commodities[commodities["commodity"]=="Coffee"].sort_values("date").iloc[-1]["price_usd"]
    kpi_wheat = commodities[commodities["commodity"]=="Wheat"].sort_values("date").iloc[-1]["price_usd"]

    # Serialize commodity data for JS interactivity
    comm_data = {}
    for c in ["Cocoa", "Coffee", "Sugar", "Wheat"]:
        d = commodities[commodities["commodity"] == c].sort_values("date")
        comm_data[c] = {"dates": d["date"].dt.strftime("%Y-%m-%d").tolist(),
                        "prices": d["price_usd"].tolist()}

    # Generate Plotly figures
    cfg = {"displayModeBar": False, "responsive": True}
    f1 = fig_commodities(commodities).to_html(full_html=False, include_plotlyjs="cdn", config=cfg, div_id="chart-commodities")
    f2 = fig_fx(fx).to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="chart-fx")
    f3 = fig_yoy_commodity(commodities).to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="chart-yoy")
    f4 = fig_inflation(inflation).to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="chart-inflation")
    f5 = fig_squeeze(pressure).to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="chart-squeeze")

    html = f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>FMCG Cost Pressure Monitor — Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:{BG};color:{TEXT};font-family:'DM Sans','Segoe UI',system-ui,sans-serif;padding:20px 24px;min-height:100vh}}
.d-header{{text-align:center;padding:24px 0 16px}}
.d-header h1{{font-size:1.5rem;font-weight:800;color:{TEXT};margin-bottom:6px}}
.d-header p{{color:{MUTED};font-size:.85rem;max-width:600px;margin:0 auto}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}}
.kpi{{background:{CARD};border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;text-align:center;transition:transform .2s}}
.kpi:hover{{transform:translateY(-2px);border-color:rgba(91,140,255,.25)}}
.kpi-v{{font-size:1.5rem;font-weight:800;margin-bottom:2px}}
.kpi-l{{font-size:.72rem;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:.04em}}
.kpi-v.c1{{color:#f59e0b}}.kpi-v.c2{{color:#ef4444}}.kpi-v.c3{{color:#3b82f6}}.kpi-v.c4{{color:#818cf8}}
.section{{margin-bottom:28px}}
.section-title{{font-size:1rem;font-weight:700;color:{TEXT};margin-bottom:6px;display:flex;align-items:center;gap:8px}}
.section-title .ico{{font-size:1.2rem}}
.section-desc{{font-size:.82rem;color:{MUTED};line-height:1.5;margin-bottom:14px;max-width:700px}}
.section-desc strong{{color:{TEXT}}}
.row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}}
.chart-card{{background:{CARD};border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px;overflow:hidden}}
.chart-full{{background:{CARD};border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:12px;overflow:hidden}}
.filter-bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:14px}}
.filter-bar label{{font-size:.78rem;color:{MUTED};font-weight:600}}
.filter-bar select{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);color:{TEXT};padding:6px 12px;border-radius:8px;font-size:.82rem;font-family:inherit;cursor:pointer;outline:none;transition:border-color .2s}}
.filter-bar select:hover{{border-color:{ACCENT}}}
.filter-bar select:focus{{border-color:{ACCENT};box-shadow:0 0 0 2px rgba(91,140,255,.15)}}
.callout{{background:rgba(91,140,255,.06);border:1px solid rgba(91,140,255,.15);border-radius:10px;padding:12px 16px;font-size:.82rem;color:{TEXT};line-height:1.5;margin-bottom:16px}}
.callout strong{{color:#5b8cff}}
.callout.warn{{background:rgba(239,68,68,.06);border-color:rgba(239,68,68,.15)}}
.callout.warn strong{{color:#ef4444}}
@media(max-width:700px){{.row{{grid-template-columns:1fr}}.kpi-row{{grid-template-columns:1fr 1fr}}}}
</style></head><body>

<div class="d-header">
  <h1>Macro Cost Pressure Monitor</h1>
  <p>Données sources : BCE (taux de change), INSEE (IPC alimentaire), Yahoo Finance (commodités agricoles), Open Food Facts (catalogue produit).</p>
</div>

<div class="kpi-row">
  <div class="kpi"><div class="kpi-v c4">{kpi_fx:.4f}</div><div class="kpi-l">EUR / USD (BCE)</div></div>
  <div class="kpi"><div class="kpi-v c1">${kpi_cocoa:,.0f}</div><div class="kpi-l">Cacao (USD/t)</div></div>
  <div class="kpi"><div class="kpi-v c2">${kpi_coffee:,.0f}</div><div class="kpi-l">Café (USD/lb)</div></div>
  <div class="kpi"><div class="kpi-v c3">${kpi_wheat:,.0f}</div><div class="kpi-l">Blé (USD/bu)</div></div>
</div>

<!-- SECTION 1: Commodity Trends -->
<div class="section">
  <div class="section-title"><span class="ico">📈</span> Tendances des Commodités Agricoles</div>
  <div class="section-desc">Évolution des prix des 4 matières premières clés du secteur FMCG. Le <strong>Cacao</strong> affiche la plus forte volatilité sur la période, suivi du <strong>Café</strong>. Ces deux commodités sont les principaux vecteurs de pression sur les marges des acteurs du chocolat, de la biscuiterie et des boissons chaudes.</div>
  <div class="filter-bar">
    <label>Commodité :</label>
    <select id="filterComm" onchange="filterCommodity()">
      <option value="all">Toutes</option>
      <option value="Cocoa">Cacao</option>
      <option value="Coffee">Café</option>
      <option value="Sugar">Sucre</option>
      <option value="Wheat">Blé</option>
    </select>
  </div>
  <div class="chart-card">{f1}</div>
</div>

<!-- SECTION 2: FX + YoY -->
<div class="section">
  <div class="section-title"><span class="ico">🌍</span> Exposition au Change & Variations Annuelles</div>
  <div class="section-desc">Le taux <strong>EUR/USD</strong> impacte directement le coût d'importation des matières cotées en dollars. En parallèle, les variations Year-over-Year (YoY) permettent d'isoler les chocs de prix récents et de quantifier la pression inflationniste transmise aux acheteurs.</div>
  <div class="row">
    <div class="chart-card">{f2}</div>
    <div class="chart-card">{f3}</div>
  </div>
</div>

<!-- SECTION 3: Inflation -->
<div class="section">
  <div class="section-title"><span class="ico">🏷️</span> Inflation Alimentaire par Catégorie (INSEE)</div>
  <div class="section-desc">Décomposition de l'<strong>IPC alimentaire français</strong> par sous-catégorie INSEE. Les catégories avec une inflation YoY positive supérieure à la moyenne signalent une transmission active des coûts matières premières au consommateur final. Les catégories en vert indiquent une absorption partielle ou une déflation structurelle.</div>
  <div class="chart-full">{f4}</div>
</div>

<!-- SECTION 4: Squeeze Matrix -->
<div class="section">
  <div class="section-title"><span class="ico">⚠️</span> Matrice de « Cost Squeeze » — Diagnostic de Marge</div>
  <div class="section-desc">Le <strong>Cost Squeeze Score</strong> mesure l'écart entre la hausse des coûts matières premières (input) et la hausse de l'IPC (output consommateur). Un score <strong>positif élevé</strong> signifie que les coûts augmentent plus vite que les prix de vente → <strong>compression de marge</strong>. Un score négatif indique un pass-through réussi.</div>
  <div class="callout warn">
    <strong>Alerte Marge :</strong> Les catégories connectées au Cacao (chocolats, biscuits) affichent les scores de squeeze les plus élevés, signalant une compression de marge critique à court terme.
  </div>
  <div class="chart-full">{f5}</div>
</div>

<script>
var commData = {json.dumps(comm_data)};
var commColors = {json.dumps(COLORS)};

function filterCommodity() {{
  var sel = document.getElementById('filterComm').value;
  var el = document.getElementById('chart-commodities');
  var data = [];
  if (sel === 'all') {{
    ['Cocoa','Coffee','Sugar','Wheat'].forEach(function(c){{
      data.push({{x:commData[c].dates, y:commData[c].prices, name:c, type:'scatter', mode:'lines',
        line:{{width:2.5, color:commColors[c]}},
        hovertemplate:'<b>'+c+'</b><br>%{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>'}});
    }});
  }} else {{
    data.push({{x:commData[sel].dates, y:commData[sel].prices, name:sel, type:'scatter', mode:'lines',
      line:{{width:2.5, color:commColors[sel]}}, fill:'tozeroy', fillcolor:commColors[sel]+'10',
      hovertemplate:'<b>'+sel+'</b><br>%{{x|%b %Y}}<br>${{y:,.0f}}<extra></extra>'}});
  }}
  Plotly.react(el, data, el.layout);
}}

(function(){{
  function send(){{
    var h=document.documentElement.scrollHeight;
    if(window.parent)window.parent.postMessage({{type:'rm-iframe-height',height:h}},'*');
  }}
  send();window.addEventListener('resize',send);setInterval(send,2000);
}})();
</script>
</body></html>"""

    out = os.path.join(os.path.dirname(__file__), "..", "..", "..", "portfolio_rafael_midolli", "reports", "dashboard_fmcg.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard saved: {os.path.abspath(out)} ({len(html):,} bytes)")


if __name__ == "__main__":
    build_portfolio_dashboard()
