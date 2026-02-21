"""
European FMCG Cost Pressure Monitor — Main Dash Application.
Reads from DuckDB-processed Parquet mart files and serves an interactive,
multi-page dashboard.
"""
import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

# ── Data Loading ─────────────────────────────────────────────────────────
MARTS = os.path.join(os.path.dirname(__file__), "..", "..", "data", "marts")

def load(filename):
    return pd.read_parquet(os.path.join(MARTS, filename))


# ── App Init ─────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    use_pages=True,
    pages_folder=os.path.join(os.path.dirname(__file__), "pages"),
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="FMCG Cost Pressure Monitor",
)

# ── Sidebar ──────────────────────────────────────────────────────────────
sidebar = dbc.Nav(
    [
        dbc.NavLink(
            [html.I(className=page.get("icon", "")), html.Span(page["name"], className="ms-2")],
            href=page["relative_path"],
            active="exact",
            className="text-white",
        )
        for page in dash.page_registry.values()
    ],
    vertical=True,
    pills=True,
    className="bg-dark pt-3 px-2",
)

# ── Layout ───────────────────────────────────────────────────────────────
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                # Header
                dbc.Col(
                    html.Div(
                        [
                            html.H2("🛒 FMCG Cost Pressure Monitor", className="text-white fw-bold mb-0"),
                            html.Small("France · Real data from INSEE, ECB, Yahoo Finance & Open Food Facts",
                                       className="text-secondary"),
                        ],
                        className="py-3 px-3",
                    ),
                    width=12,
                    className="bg-dark border-bottom border-secondary",
                ),
            ]
        ),
        dbc.Row(
            [
                # Sidebar
                dbc.Col(sidebar, width=2, className="bg-dark min-vh-100 border-end border-secondary"),
                # Page content
                dbc.Col(dash.page_container, width=10, className="p-4"),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
    className="bg-dark min-vh-100",
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
