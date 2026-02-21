"""
Page 2 — Ingredient Cost Shock
Highlights which raw materials have seen the largest price spikes,
and correlates them with consumer inflation categories.
"""
import os, dash, pandas as pd, plotly.express as px
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/cost-shock", name="📈 Cost Shock", order=1)

MARTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "marts")

df_comm = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))
df_mart = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))

# ── YoY heatmap of commodity changes ─────────────────────────────────────
df_heat = df_comm.dropna(subset=["yoy_change_pct"]).copy()
df_heat["month"] = df_heat["date"].dt.strftime("%Y-%m")

fig_heat = px.density_heatmap(
    df_heat, x="month", y="commodity", z="yoy_change_pct",
    color_continuous_scale="RdYlGn_r",
    title="Commodity YoY Price Change (%) — Heatmap",
    template="plotly_dark",
    labels={"yoy_change_pct": "YoY %", "month": "", "commodity": ""},
)
fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

# ── Bar chart: latest YoY change per commodity ───────────────────────────
latest = df_comm.dropna(subset=["yoy_change_pct"]).groupby("commodity").last().reset_index()
latest["color"] = latest["yoy_change_pct"].apply(lambda x: "crimson" if x > 0 else "mediumseagreen")

fig_bar = px.bar(
    latest.sort_values("yoy_change_pct", ascending=True),
    x="yoy_change_pct", y="commodity", orientation="h",
    title="Latest YoY Price Change by Commodity",
    template="plotly_dark",
    color="yoy_change_pct",
    color_continuous_scale="RdYlGn_r",
    labels={"yoy_change_pct": "YoY Change %", "commodity": ""},
)
fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      showlegend=False)

# ── Pressure: commodity vs inflation side-by-side ────────────────────────
fig_pressure = px.scatter(
    df_mart.dropna(subset=["commodity_yoy_pct", "yoy_inflation_pct"]),
    x="commodity_yoy_pct", y="yoy_inflation_pct",
    color="commodity", size_max=10,
    title="Input Cost Change vs Consumer Inflation (per month)",
    template="plotly_dark",
    labels={"commodity_yoy_pct": "Commodity YoY %", "yoy_inflation_pct": "CPI YoY %"},
)
fig_pressure.add_shape(type="line", x0=-100, y0=-100, x1=200, y1=200,
                       line=dict(dash="dot", color="grey"))
fig_pressure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


layout = html.Div([
    html.H3("Ingredient Cost Shock Analysis", className="text-white mb-3"),
    html.P("Tracking raw material price surges and their link to retail food inflation.",
           className="text-secondary mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_bar, config={"displayModeBar": False}), md=5),
        dbc.Col(dcc.Graph(figure=fig_heat, config={"displayModeBar": False}), md=7),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_pressure, config={"displayModeBar": False}), md=12),
    ]),
    dbc.Alert(
        "Points above the diagonal line indicate that consumer prices rose FASTER than input costs "
        "(retailers/brands passed costs through). Points below indicate a cost squeeze.",
        color="info", className="mt-3",
    ),
])
