"""
Page 3 — Consumer Inflation Translation
Overlays commodity input costs with INSEE's Food CPI to show
whether raw material increases are being passed on to consumers.
"""
import os, dash, pandas as pd, plotly.express as px, plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/inflation", name="🏷️ Inflation Translation", order=2)

MARTS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "marts")

df_mart = pd.read_parquet(os.path.join(MARTS, "mart_category_pressure.parquet"))
df_infl = pd.read_parquet(os.path.join(MARTS, "fact_inflation.parquet"))

# ── Dropdown options: inflation categories ───────────────────────────────
categories = sorted(df_mart["inflation_category"].unique())

layout = html.Div([
    html.H3("Consumer Inflation Translation", className="text-white mb-3"),
    html.P("Are input cost increases being passed through to French consumers?",
           className="text-secondary mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Select CPI Category", className="text-white"),
            dcc.Dropdown(
                id="inflation-cat-dropdown",
                options=[{"label": c, "value": c} for c in categories],
                value=categories[0] if categories else None,
                clearable=False,
                className="mb-3",
            ),
        ], md=4),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="inflation-vs-commodity-chart"), md=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="squeeze-score-chart"), md=12),
    ]),
])


@callback(
    Output("inflation-vs-commodity-chart", "figure"),
    Output("squeeze-score-chart", "figure"),
    Input("inflation-cat-dropdown", "value"),
)
def update_charts(selected_category):
    filtered = df_mart[df_mart["inflation_category"] == selected_category].copy()
    filtered = filtered.sort_values("date")

    # ── Dual-axis: commodity price vs CPI ────────────────────────────────
    fig = go.Figure()
    for commodity in filtered["commodity"].unique():
        sub = filtered[filtered["commodity"] == commodity]
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["commodity_yoy_pct"],
            name=f"{commodity} (Input Cost YoY %)",
            mode="lines+markers",
            line=dict(width=2),
        ))

    fig.add_trace(go.Scatter(
        x=filtered["date"], y=filtered["yoy_inflation_pct"],
        name=f"CPI: {selected_category} (YoY %)",
        mode="lines",
        line=dict(width=3, dash="dash", color="white"),
    ))

    fig.update_layout(
        title=f"Input Costs vs Consumer Inflation: {selected_category}",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="YoY Change %",
        legend=dict(orientation="h", y=-0.2),
    )

    # ── Cost squeeze score over time ─────────────────────────────────────
    fig2 = px.bar(
        filtered, x="date", y="cost_squeeze_score", color="commodity",
        title=f"Cost Squeeze Score: {selected_category}",
        template="plotly_dark",
        labels={"cost_squeeze_score": "Squeeze Score (Input - CPI)", "date": ""},
        barmode="group",
    )
    fig2.add_hline(y=0, line_dash="dash", line_color="grey")
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       legend=dict(orientation="h", y=-0.2))

    return fig, fig2
