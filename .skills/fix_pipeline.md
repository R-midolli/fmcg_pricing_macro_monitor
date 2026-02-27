# Skill: fix_pipeline

## Quando usar
Quando o usuário pedir para corrigir, rodar ou debugar o pipeline de dados.
Ler este arquivo completo antes de tocar em qualquer código.

---

## BUG 1 — Preços em centavos (confirmado no JSON atual)

O `data/dashboard_fmcg_data.json` atual mostra valores errados:

| Commodity | Valor no JSON | Correto       |
|-----------|--------------|---------------|
| Coffee    | ~287         | ~2.87 USD/lb  |
| Sugar     | ~13.8        | ~0.138 USD/lb |
| Wheat     | ~580         | ~5.80 USD/bu  |
| Cocoa     | ~3072 ✓      | ~3072 USD/ton |

**Causa:** yfinance retorna KC=F, SB=F, ZW=F em centavos. CC=F já está correto.

**Fix em `src/extract/commodities_api.py`:**
```python
CENTS_TICKERS = {"KC=F", "SB=F", "ZW=F"}

def download_commodity(ticker: str, period: str = "2y") -> pd.DataFrame:
    # Usar Ticker.history() — yf.download() retorna MultiIndex no yfinance 1.2.0
    # e df["Close"] fica NaN silenciosamente
    t = yf.Ticker(ticker)
    df = t.history(period=period, auto_adjust=True)
    if df.empty:
        raise ValueError(f"Sem dados para {ticker}")
    if ticker in CENTS_TICKERS:
        df[["Open", "High", "Low", "Close"]] /= 100
    return df
```

**Ranges esperados para validação:**
```python
COMMODITY_PRICE_RANGES = {
    "Coffee": (1.0,  6.0),    # USD/lb
    "Sugar":  (0.08, 0.35),   # USD/lb
    "Wheat":  (3.5,  9.0),    # USD/bu
    "Cocoa":  (1500, 15000),  # USD/ton — não dividir
}
```

---

## BUG 2 — EUR/USD stale

O JSON mostra `kpis.fx_eur_usd: 1.1834` mas o valor real (fev 2026) é ~1.04.
Investigar `src/extract/ecb_api.py` — verificar se há cache ou se a URL da ECB
está buscando dados históricos em vez dos mais recentes.

---

## CONTRATO JSON — nomes são lidos diretamente pelo dashboard_fmcg.js

```python
from datetime import datetime, timezone

output = {
    "metadata": {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    },
    "kpis": {
        "fx_eur_usd": float(eurusd_latest),  # ← underscore obrigatório
    },
    "charts": {
        "commodities": {
            "Cocoa":  {"dates": [...], "prices": [...]},  # USD/ton
            "Coffee": {"dates": [...], "prices": [...]},  # USD/lb após /100
            "Sugar":  {"dates": [...], "prices": [...]},  # USD/lb após /100
            "Wheat":  {"dates": [...], "prices": [...]},  # USD/bu após /100
        },
        "fx":                   {"dates": [...], "values": [...]},
        "yoy_commodity":        {"labels": [...], "values": [...]},
        "yoy_inflation":        {"labels": [...], "values": [...]},
        "inflation_timeseries": {"Category": {"dates": [...], "values": [...]}},
        "squeeze_matrix":       {"x_labels": [...], "y_labels": [...], "z_values": [[...]]},
        "momentum": {
            "Cocoa":  {"dates": [...], "prices": [...]},
            "Coffee": {"dates": [...], "prices": [...]},
            "Sugar":  {"dates": [...], "prices": [...]},
            "Wheat":  {"dates": [...], "prices": [...]},
        }
    }
}
# Salvar em: data/dashboard_fmcg_data.json
# Copiar para: ../portfolio_rafael_midolli/reports/dashboard_fmcg_data.json
```

---

## MAPA DO PROJETO

```
src/extract/commodities_api.py          ← BUG centavos — corrigir aqui
src/extract/ecb_api.py                  ← verificar staleness
src/transform/build_marts.py            ← lê data/raw/, escreve data/marts/
src/dashboard/generate_portfolio_report.py  ← gera o JSON final
tests/test_pipeline.py                  ← adicionar testes nesta sessão
```

Package manager: `uv` — sempre `uv run python src/...`
Python: 3.13

**Dois dashboards — não confundir:**
- `data/dashboard_fmcg.html` → app Dash local, não é o portfolio
- `portfolio/reports/dashboard_fmcg_data.json` → JSON estático para o ECharts do portfolio

---

## Checklist de saída
- [ ] Coffee ~2-4 USD/lb (não 280-400)
- [ ] Sugar ~0.10-0.20 USD/lb (não 13-15)
- [ ] Wheat ~5-6 USD/bu (não 500-600)
- [ ] EUR/USD ~1.04 (não 1.18)
- [ ] JSON tem `kpis.fx_eur_usd` com underscore
- [ ] JSON tem `metadata.last_updated` em ISO 8601
- [ ] `uv run pytest tests/` passa sem erros
