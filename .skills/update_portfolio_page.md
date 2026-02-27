# Skill: update_portfolio_page

## Quando usar
Quando o usuário pedir para editar `project-pricing.html` no portfolio.

**Regra de ouro:** `dashboard_fmcg.js` está completo e funcional — NÃO reescrever.
Apenas adicionar HTML/CSS e pequenos blocos JS que se encaixam no existente.

---

## Convenções CSS/JS do portfolio

### Variáveis CSS reais (project.css)
```
--accent: #5b8cff   --accent-2: #8b5cf6   --radius: 20px
--surface: rgba(255,255,255,.06)   --border: rgba(255,255,255,.08)
--text-muted: #7a8494
--font-head: 'Playfair Display'    --font-body: 'DM Sans'
```

### Bilingual pattern — SEMPRE este formato
```html
<span class="lang-fr">texto em francês</span>
<span class="lang-en">text in English</span>
```
CSS já faz o hide via `[data-lang="fr"] .lang-en { display:none }`.
**Nunca usar JS para esconder/mostrar manualmente.**

### API de idioma (shared.js)
```javascript
window.__rm.getLang()   // retorna 'fr' ou 'en'
document.addEventListener('langchange', e => { e.detail.lang });
document.documentElement.dataset.theme  // 'dark' ou 'light'
```

### Classes existentes — não recriar inline
`.card` `.bento-grid` `.bento-item` `.kpi-huge` `.metrics-mini` `.metric-mini`
`.tech-tag` `.btn-github` (tem width:100% por padrão — sobrescrever com `style="width:auto"`)
`.insight-card` `.bullets` `.bullet` `.bullet-details` `.conclusion--highlight`
`.category-toggle` `.chart-native-container` `.insight-block`

---

## Estrutura DOM de project-pricing.html

```
<main class="main">
  <header class="case-header">
    <div class="case-label">
    <h1 class="case-title">
    <p class="case-subtitle">
    ← INSERIR badge last-updated AQUI

  <section class="bento-grid">
    col-8  → Problématique + flow-nodes
    col-4  → #kpi-title / #kpi-value / #kpi-desc
    col-12 → Arquitetura (4 .arch-step) + btn-github
    col-6  → #kpi-val-fx  (EUR/USD)
    col-6  → #spot-title / #spot-value / #spot-desc

  <section class="card">  ← dashboard principal
    .dashboard-header [título + .category-toggle × 5]
    .bento-grid:
      #chart-commodities (col-12)
      #chart-fx (col-6)   #chart-yoy (col-6)
      #chart-inflation (col-12)
      #dynamic-insight (col-12)
      #chart-squeeze (col-12)
      #chart-momentum + .momentum-toggle × 5 (col-12)

  <section class="conclusion conclusion--highlight">
    3 parágrafos Key Takeaways

  ← INSERIR CTA AQUI

</main>
<!-- ordem obrigatória: echarts → shared.js → dashboard_fmcg.js -->
```

---

## O que adicionar nesta sessão

### A — Fix de texto
```
BUSCAR:  Quand le prix du Cacao triple
TROCAR:  Quand le prix du Cacao a quadruplé

BUSCAR:  When cocoa prices triple
TROCAR:  When cocoa prices quadrupled
```

### B — Badge last-updated

HTML (após `<p class="case-subtitle">`, dentro do `<header>`):
```html
<div style="margin-top:14px;display:flex;justify-content:center;">
  <span class="last-updated-badge">
    <span class="lang-fr">Données au</span>
    <span class="lang-en">Data as of</span>
    <strong id="last-updated-date">—</strong>
  </span>
</div>
```

CSS (adicionar no `<style>` inline da página):
```css
.last-updated-badge {
    display:inline-flex;align-items:center;gap:6px;font-size:.75rem;
    color:var(--text-muted);padding:4px 12px;border-radius:999px;
    border:1px solid var(--border);background:var(--surface);
}
.last-updated-badge strong { color:var(--accent);font-weight:600; }
```

JS (adicionar em `dashboard_fmcg.js`, dentro do `try{}`, após `updateDynamicKPI()`):
```javascript
function formatUpdateDate(iso, lang) {
    const d = new Date(iso);
    return lang === 'en'
        ? d.toLocaleDateString('en-GB', {day:'2-digit',month:'short',year:'numeric'})
        : d.toLocaleDateString('fr-FR', {day:'2-digit',month:'long',year:'numeric'});
}
function refreshLastUpdated(lang) {
    const el = document.getElementById('last-updated-date');
    if (!el || !data?.metadata?.last_updated) return;
    el.textContent = formatUpdateDate(data.metadata.last_updated, lang);
}
refreshLastUpdated(window.__rm ? window.__rm.getLang() : 'fr');
document.addEventListener('langchange', e => refreshLastUpdated(e.detail.lang));
```

### C — CTA no final

HTML (após `</section>` da `conclusion--highlight`, antes de `</main>`):
```html
<div class="fmcg-cta" style="margin-top:32px;">
  <div class="fmcg-cta-text">
    <strong>
      <span class="lang-fr">Vous opérez dans l'agroalimentaire ?</span>
      <span class="lang-en">Operating in FMCG or food industry?</span>
    </strong>
    <p>
      <span class="lang-fr">Ce type d'analyse peut être adapté à vos données internes en quelques jours.</span>
      <span class="lang-en">This analysis can be adapted to your internal data within days.</span>
    </p>
  </div>
  <div class="fmcg-cta-actions">
    <a href="index.html#contact" class="btn-github"
       style="width:auto;margin-top:0;padding:11px 22px;font-size:.9rem;">
      <span class="lang-fr">Discutons →</span>
      <span class="lang-en">Let's talk →</span>
    </a>
    <a href="https://github.com/R-midolli/fmcg_pricing_macro_monitor"
       target="_blank" rel="noopener" class="btn-back"
       style="padding:11px 22px;font-size:.9rem;color:var(--text);">
      <span class="lang-fr">Voir le code</span>
      <span class="lang-en">View code</span>
    </a>
  </div>
</div>
```

CSS (adicionar no `<style>` inline):
```css
.fmcg-cta {
    display:flex;justify-content:space-between;align-items:center;
    gap:24px;flex-wrap:wrap;padding:28px 32px;background:var(--surface);
    border:1px solid var(--border);border-top:3px solid var(--accent);
    border-radius:var(--radius);
}
.fmcg-cta-text p { font-size:.85rem;color:var(--text-muted);margin-top:6px; }
.fmcg-cta-actions { display:flex;gap:12px;flex-wrap:wrap;flex-shrink:0; }
@media(max-width:640px){
    .fmcg-cta{flex-direction:column;align-items:flex-start;padding:20px;}
}
```

---

## Checklist de saída
- [ ] "triple" → "quadruplé/quadrupled" corrigido
- [ ] Badge last-updated visível no header da página
- [ ] Badge atualiza ao trocar idioma FR/EN
- [ ] CTA visível no final da página com links funcionais
- [ ] Testar no Live Server porta 5501 antes de commitar
