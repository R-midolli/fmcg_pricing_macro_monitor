# Skill: setup_cicd

## Quando usar
Quando o usuário pedir para criar o pipeline automático, GitHub Actions
ou deploy automático para o portfolio.

Ler `fix_pipeline.md` primeiro para entender o fluxo de execução.

---

## Arquivo a criar: `.github/workflows/data_pipeline.yml`

```yaml
name: FMCG Data Pipeline

on:
  schedule:
    - cron: '0 6 * * 1'  # toda segunda-feira 06:00 UTC
  workflow_dispatch:       # permite rodar manualmente

jobs:
  update-data:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v3
        with:
          python-version: '3.13'

      - run: uv sync

      - run: uv run python src/extract/ecb_api.py
      - run: uv run python src/extract/commodities_api.py
      - run: uv run python src/extract/insee_api.py
      - run: uv run python src/extract/openfoodfacts_api.py
        continue-on-error: true  # fonte não-crítica

      - run: uv run python src/transform/build_marts.py

      - name: Testes — bloqueia deploy se falhar
        run: uv run pytest tests/ -v --tb=short

      - name: Gerar JSON
        run: |
          uv run python src/dashboard/generate_portfolio_report.py
          test -f data/dashboard_fmcg_data.json || \
            (echo "❌ JSON não gerado" && exit 1)

      - name: Deploy para portfolio
        env:
          PORTFOLIO_TOKEN: ${{ secrets.PORTFOLIO_DEPLOY_TOKEN }}
        run: |
          git config --global user.name  "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git clone \
            https://x-access-token:${PORTFOLIO_TOKEN}@github.com/R-midolli/portfolio_rafael_midolli.git \
            /tmp/portfolio
          cp data/dashboard_fmcg_data.json \
             /tmp/portfolio/reports/dashboard_fmcg_data.json
          cd /tmp/portfolio
          git add reports/dashboard_fmcg_data.json
          if git diff --staged --quiet; then
            echo "Sem mudanças — nada a commitar"
          else
            git commit -m "chore(data): fmcg auto-update $(date +%Y-%m-%d)"
            git push
          fi
```

---

## Instrução manual para Rafael (o agente não consegue fazer por ele)

```
PASSO 1 — Criar Personal Access Token:
  https://github.com/settings/tokens
  → Generate new token (classic)
  → Scope: marcar "repo" (full control)
  → Expiration: No expiration (ou 1 year)
  → Copiar o token (começa com ghp_...)

PASSO 2 — Adicionar como Secret no repo FMCG:
  https://github.com/R-midolli/fmcg_pricing_macro_monitor/settings/secrets/actions
  → New repository secret
  → Name:  PORTFOLIO_DEPLOY_TOKEN
  → Value: (colar o token do passo 1)

PASSO 3 — Testar:
  https://github.com/R-midolli/fmcg_pricing_macro_monitor/actions
  → "FMCG Data Pipeline" → Run workflow → verificar se todos os steps ficam verdes
```

---

## Checklist de saída
- [ ] `.github/workflows/data_pipeline.yml` criado
- [ ] Usa `astral-sh/setup-uv@v3` com `python-version: '3.13'`
- [ ] Testes rodam ANTES do step de deploy
- [ ] Secret `PORTFOLIO_DEPLOY_TOKEN` referenciado (não hardcoded)
- [ ] Instruções dos 3 passos mostradas ao usuário
