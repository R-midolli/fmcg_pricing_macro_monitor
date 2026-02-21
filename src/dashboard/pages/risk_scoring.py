"""
Page 4 — Category Risk Exposure
Heatmap and table showing which Open Food Facts product categories
are most vulnerable to current commodity and FX pressures.
"""
import os, dash, pandas as pd, plotly.express as px
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/risk", name="⚠️ Category Risk", order=3)

MARTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "marts")

df_prod = pd.read_parquet(os.path.join(MARTS, "dim_product.parquet"))
df_mart = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))
df_comm = pd.read_parquet(os.path.join(MARTS, "fact_commodities.parquet"))

# ── Compute risk scores per commodity exposure ───────────────────────────
# Latest commodity YoY change
latest_comm = df_comm.dropna(subset=["yoy_change_pct"]).groupby("commodity").last().reset_index()
latest_comm = latest_comm[["commodity", "yoy_change_pct"]].rename(
    columns={"yoy_change_pct": "commodity_yoy_pct"}
)

# Count products by commodity exposure
prod_exposure = df_prod.groupby("primary_commodity_exposure").agg(
    product_count=("product_id", "count"),
    sample_brands=("brand", lambda x: ", ".join(x.dropna().unique()[:5])),
).reset_index().rename(columns={"primary_commodity_exposure": "commodity"})

# Merge
risk_df = prod_exposure.merge(latest_comm, on="commodity", how="left")
risk_df["commodity_yoy_pct"] = risk_df["commodity_yoy_pct"].fillna(0).round(1)

# Risk level
def risk_level(yoy):
    if yoy > 30: return "🔴 Critical"
    if yoy > 10: return "🟠 High"
    if yoy > 0:  return "🟡 Moderate"
    return "🟢 Low"

risk_df["risk_level"] = risk_df["commodity_yoy_pct"].apply(risk_level)
risk_df = risk_df.sort_values("commodity_yoy_pct", ascending=False)

# ── Bar chart ────────────────────────────────────────────────────────────
fig_risk = px.bar(
    risk_df[risk_df["commodity"] != "Other"],
    x="commodity", y="commodity_yoy_pct",
    color="commodity_yoy_pct",
    color_continuous_scale="RdYlGn_r",
    text="product_count",
    title="Product Exposure by Commodity — Latest YoY Price Change",
    template="plotly_dark",
    labels={"commodity_yoy_pct": "Commodity YoY %", "commodity": "", "product_count": "# Products"},
)
fig_risk.update_traces(texttemplate="%{text} products", textposition="outside")
fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       showlegend=False)

# ── Latest squeeze scores by category from mart ─────────────────────────
latest_squeeze = df_mart.dropna(subset=["cost_squeeze_score"]).groupby(
    ["inflation_category", "commodity"]
).last().reset_index()

fig_squeeze_heat = px.imshow(
    latest_squeeze.pivot_table(index="inflation_category", columns="commodity",
                                values="cost_squeeze_score", aggfunc="mean").fillna(0),
    color_continuous_scale="RdBu_r",
    title="Cost Squeeze Heatmap (Input Cost Rise − CPI Rise)",
    template="plotly_dark",
    aspect="auto",
    labels={"color": "Squeeze Score"},
)
fig_squeeze_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


layout = html.Div([
    html.H3("Category Risk Exposure", className="text-white mb-3"),
    html.P("Mapping Open Food Facts product categories to commodity cost pressures.",
           className="text-secondary mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_risk, config={"displayModeBar": False}), md=6),
        dbc.Col(dcc.Graph(figure=fig_squeeze_heat, config={"displayModeBar": False}), md=6),
    ], className="mb-4"),

    html.H5("Product Risk Detail", className="text-white mt-4 mb-3"),
    dash_table.DataTable(
        id="risk-table",
        columns=[
            {"name": "Commodity Exposure", "id": "commodity"},
            {"name": "# Products", "id": "product_count"},
            {"name": "Commodity YoY %", "id": "commodity_yoy_pct"},
            {"name": "Risk Level", "id": "risk_level"},
            {"name": "Sample Brands", "id": "sample_brands"},
        ],
        data=risk_df.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#303030", "color": "white", "fontWeight": "bold"},
        style_cell={"backgroundColor": "#222", "color": "white", "border": "1px solid #444",
                    "textAlign": "left", "padding": "8px", "maxWidth": "300px", "overflow": "hidden",
                    "textOverflow": "ellipsis"},
        style_data_conditional=[
            {"if": {"filter_query": '{commodity_yoy_pct} > 30'}, "backgroundColor": "#5c1a1a"},
            {"if": {"filter_query": '{commodity_yoy_pct} > 10 && {commodity_yoy_pct} <= 30'},
             "backgroundColor": "#5c3a1a"},
        ],
        page_size=10,
    ),
])
