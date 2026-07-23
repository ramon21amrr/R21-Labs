---
name: lvfi-pricing-engine
description: Protege versões, matemática congelada, contratos, schemas, hashes e gates do Pricing Engine LVFI em qualquer tarefa que o alcance.
compatibility: opencode
metadata:
  owner: R21 Labs
  product: LVFI Pricing Engine
---

# Pricing Engine LVFI

Estado qualificado desta configuração: distribuição `1.1.0a9`; matemática do
engine `1.0.0`; 519 testes; 100% de statements e branches.

Leia `packages/pricing-engine/README.md`, `pyproject.toml`,
`docs/products/linha-de-valor-football-intelligence/12-dynamic-audit-and-mathematical-baseline.md`,
`13-pricing-engine-technical-plan.md`, `14-pricing-engine-final-validation.md` e
ADRs LVFI aplicáveis.

Nunca altere matemática, contratos, schemas, hashes, catálogo, versões ou
`requirements-dev.lock` fora de escopo explícito. Use apenas o venv autorizado.
Confirme a regressão 10×10 e os hashes pelos testes originais; não copie
expectativas para fazê-las passar.
