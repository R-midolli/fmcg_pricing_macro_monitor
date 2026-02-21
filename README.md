# 🛒 FMCG Cost Pressure Monitor

> **Analyse macro-économique en temps réel des pressions sur les coûts (Cost Squeeze) du secteur FMCG.**
> Construit avec 100% de données réelles provenant d'APIs publiques.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-orange)
![ECharts](https://img.shields.io/badge/Apache_ECharts-Dashboard-green)
![CI/CD](https://img.shields.io/badge/Actions-GitHub-blueviolet)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🎯 Contexte Stratégique

Le secteur européen des produits de grande consommation (FMCG) fait face à des pressions historiques sur les coûts liées à :
- **La volatilité des prix des matières premières agricoles** (Cacao, Café, Blé, Sucre)
- **Les fluctuations du taux de change EUR/USD** qui ont un impact sur les coûts d'importation
- **L'inflation des prix à la consommation**, mesurée par l'IPC de l'INSEE

Ce projet monitorize ces variables en temps réel et répond à :
- Les coûts des matières premières sont-ils répercutés sur les consommateurs ?
- Quelles catégories de produits sont les plus exposées aux chocs des cours mondiaux ?
- Quelle est la "compression des marges" (Cost Squeeze) entre l'inflation industrielle et les prix de détail ?

---

## 📊 Sources de Données (APIs 100% Réelles)

| Source | Données | API |
|--------|---------|-----|
| **Banque Centrale Européenne** | Taux de change EUR/USD quotidien | [ECB Data Portal](https://data.ecb.europa.eu/) |
| **INSEE** | Indices des Prix à la Consommation (IPC) par catégorie alimentaire | [INSEE BDM SDMX](https://bdm.insee.fr/) |
| **Yahoo Finance** | Cours des matières premières (Cacao, Café, Sucre, Blé) | [yfinance](https://pypi.org/project/yfinance/) |
| **Open Food Facts** | Catalogue de produits FMCG (marques, catégories, Nutri-Score) | [API Open Food Facts](https://world.openfoodfacts.org/) |

---

## 🏗️ Architecture Stack

```
APIs (BCE, INSEE, Yahoo Finance, Open Food Facts)
        │
        ▼
  src/extract/          → Fichiers Parquet bruts (data/raw/)
        │
        ▼
  src/transform/        → Modèle en Étoile DuckDB (data/marts/)
  (build_marts.py)        dim_date, dim_product,
                          fact_commodities, fact_inflation, fact_fx
                          mart_category_pressure
        │
        ▼
  reports/              → Export des données structurées
  dashboard JSON          pour le front-end du portfólio (ECharts)
```

**Orchestration & CI/CD** : GitHub Actions (`.github/workflows/data_pipeline.yml`) — Pipeline planifié de mise à jour hebdomadaire.

---

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.12+
- Gestionnaire de paquets [uv](https://docs.astral.sh/uv/)

### 1. Installer les dépendances
```bash
uv sync
```

### 2. Extraire les données des APIs
```bash
uv run python src/extract/ecb_api.py
uv run python src/extract/insee_api.py
uv run python src/extract/commodities_api.py
uv run python src/extract/openfoodfacts_api.py
```

### 3. Exécuter les transformations DuckDB
```bash
uv run python src/transform/build_marts.py
```

### 4. Exécuter les tests de qualité des données
```bash
uv run pytest tests/ -v
```

---

## 📁 Structure du Projet

```
fmcg_pricing_macro_monitor/
├── .github/workflows/     # Pipeline CI/CD automatisé (màj hebdo)
├── data/
│   ├── raw/               # Fichiers Parquet depuis les APIs
│   └── marts/             # Tables modélisées via DuckDB
├── reports/               # Données exportées pour le front-end
├── src/
│   ├── extract/           # Scripts d'extraction
│   │   ├── ecb_api.py
│   │   ├── insee_api.py
│   │   ├── commodities_api.py
│   │   └── openfoodfacts_api.py
│   └── transform/
│       └── build_marts.py # Création du Data Warehouse DuckDB
├── tests/                 # Scripts de validation via pytest
├── pyproject.toml
├── .gitignore
└── .env.example
```

---

## 🧠 Concepts Analytiques Clés

- **Score de "Cost Squeeze"** = YoY % Matières Premières − YoY % IPC
  - *Positif* → Les coûts d'entrée augmentent plus vite que les prix de vente (compression de la marge).
  - *Négatif* → Les distributeurs absorbent ou répercutent la baisse des coûts aux consommateurs.
- **Exposition aux Matières Premières** — Mappage des catégories Open Food Facts vers les cours correspondants.
- **Analyse en Glissement Annuel (YoY)** — Toutes les mesures sont calculées en variations sur une période de 12 mois.

---

## 📜 Licence

MIT
