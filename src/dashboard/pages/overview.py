"""
Page 1 — Global Macro Environment
KPIs and trend charts for commodities and EUR/USD.
"""
import os, dash, pandas as pd, plotly.express as px, plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="🌍 Macro Overview", order=0)

MARTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "marts")

df_comm = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))
df_fx   = pd.read_parquet(os.path.join(MARTS, "fact_fx.parquet"))
df_infl = pd.read_parquet(os.path.join(MARTS, "fact_inflation.parquet"))

# Latest values for KPIs
def _kpi(label, value, delta=None):
    delta_el = []
    if delta is not None:
        color = "text-danger" if delta > 0 else "text-success"
        arrow = "▲" if delta > 0 else "▼"
        delta_el = [html.Span(f" {arrow} {abs(delta):.1f}% YoY", className=f"small {color}")]
    return dbc.Card(
        dbc.CardBody([
            html.P(label, className="text-secondary mb-1 small"),
            html.H4([f"{value}", *delta_el], className="text-white mb-0"),
        ]),
        className="bg-dark border-secondary",
    )

latest_fx = df_fx.dropna(subset=["fx_eur_usd"]).iloc[-1]
latest_infl = df_infl[df_infl["category"] == "All Items"].dropna(subset=["yoy_inflation_pct"]).iloc[-1]

# Build KPI cards
kpi_cards = dbc.Row([
    dbc.Col(_kpi("EUR / USD", f"{latest_fx['fx_eur_usd']:.4f}",
                 latest_fx.get("yoy_change_pct")), md=3),
    dbc.Col(_kpi("France CPI (All Items)", f"{latest_infl['cpi_index']:.1f}",
                 latest_infl.get("yoy_inflation_pct")), md=3),
], className="mb-4 g-3")

# Add commodity KPIs dynamically
for commodity in df_comm["commodity"].unique():
    sub = df_comm[df_comm["commodity"] == commodity].dropna(subset=["price_usd"])
    if sub.empty:
        continue
    row = sub.iloc[-1]
    kpi_cards.children.append(
        dbc.Col(_kpi(f"{commodity} (USD)", f"{row['price_usd']:.1f}", row.get("yoy_change_pct")), md=3)
    )

# Commodity trend chart
fig_comm = px.line(
    df_comm, x="date", y="price_usd", color="commodity",
    title="Agricultural Commodity Prices (USD)",
    template="plotly_dark",
    labels={"price_usd": "Price (USD)", "date": ""},
)
fig_comm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=-0.15))

# FX trend chart
fig_fx = px.line(
    df_fx, x="date", y="fx_eur_usd",
    title="EUR/USD Exchange Rate",
    template="plotly_dark",
    labels={"fx_eur_usd": "EUR/USD", "date": ""},
)
fig_fx.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

# Inflation trend chart
fig_infl = px.line(
    df_infl, x="date", y="yoy_inflation_pct", color="category",
    title="France CPI — Year-over-Year Inflation (%)",
    template="plotly_dark",
    labels={"yoy_inflation_pct": "YoY Inflation %", "date": ""},
)
fig_infl.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=-0.25))

layout = html.Div([
    html.H3("Global Macro Environment", className="text-white mb-3"),
    html.P("Real-time macroeconomic indicators impacting the French FMCG sector.",
           className="text-secondary mb-4"),
    kpi_cards,
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_comm, config={"displayModeBar": False}), md=6),
        dbc.Col(dcc.Graph(figure=fig_fx, config={"displayModeBar": False}), md=6),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_infl, config={"displayModeBar": False}), md=12),
    ]),
])
