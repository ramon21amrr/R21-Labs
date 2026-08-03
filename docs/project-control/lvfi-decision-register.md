# Registro de decisões do LVFI

Este registro aponta decisões e conflitos; não substitui ADRs nem documentos
normativos.

| ID | Estado | Decisão | Responsável/data | Impacto | Autoridade |
| --- | --- | --- | --- | --- | --- |
| `GOV-D-001` | Aprovada | Git e documentos versionados são a memória oficial; conversa não pode ser fonte única de continuidade | Product Owner, 2026-08-02 | Estado, roadmap, decisões e próxima ação passam a ter artefatos obrigatórios | R21-GOV-001 e [Company Context](../company/company-context.md) |
| `GOV-D-002` | Aprovada | Nenhuma task futura encerra institucionalmente sem atualizar o sistema de continuidade | Product Owner, 2026-08-02 | Checklist e handoff passam a integrar o Definition of Done institucional | R21-GOV-001 e [workflow](lvfi-continuity-workflow.md) |
| `GOV-D-003` | Aprovada | `LVFI-APP-010` é a próxima task oficial | Product Owner, 2026-08-02 | Primeira interface utilizável após integração desta governança | R21-GOV-001 |
| `GOV-D-004` | Planejada | `LVFI-APP-011` é a próxima etapa planejada, sem detalhamento nesta task | Product Owner, 2026-08-02 | Preserva a direção mercado/comparação sem autorizar implementação | R21-GOV-001 |
| `GOV-D-005` | Aprovada | `LVFI-ENG-004` permanece o ID oficial da correção de estabilidade numérica do PR #4; não será reutilizado para Método 2 | Product Owner, 2026-08-02 | Histórico publicado preservado; referências antigas corrigidas | [Documento 29](../products/linha-de-valor-football-intelligence/29-lvfi-eng-004-total-market-numerical-stability.md), Git e R21-GOV-001 |
| `GOV-D-006` | Aprovada | Método 2 permanece sem novo ID nesta task | Product Owner, 2026-08-02 | Agentes não podem inferir ou criar identificador | R21-GOV-001 |
| `GOV-D-007` | Aprovada | Encerrar institucionalmente a R21-GOV-001 após sua publicação e integração pelo PR #15 no merge `a1610c85282e5d46ffc2b8094462d00d5135ca01` | Product Owner, 2026-08-02 | Não há task ativa; APP-010 passa a ser a ação imediata após a publicação deste encerramento | R21-GOV-001 e histórico Git |
| `ARCH-011` | Aprovada | Monólito modular com Next.js/TypeScript, FastAPI/Python, PostgreSQL, worker e objetos S3-compatíveis | Product Owner/ADR | Define a aplicação sem criar microsserviços | [ADR-LVFI-011](../architecture/decisions/ADR-LVFI-011-stack-e-monolito-modular-da-aplicacao.md) |
| `ARCH-012` | Aprovada | Aplicação chama a fachada pública do Pricing Engine sem duplicar matemática | Product Owner/ADR | Preserva versões, schemas, hashes e isolamento | [ADR-LVFI-012](../architecture/decisions/ADR-LVFI-012-fronteira-da-aplicacao-com-o-pricing-engine.md) |
| `ARCH-013` | Aprovada | PostgreSQL é fonte transacional; jobs persistidos e fornecedores isolados | Product Owner/ADR | Orienta persistência e integrações futuras | [ADR-LVFI-013](../architecture/decisions/ADR-LVFI-013-persistencia-jobs-e-integracoes-externas.md) |

## Conflito documental R21-GOV-001

Os [documentos 11](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md)
e [13](../products/linha-de-valor-football-intelligence/13-pricing-engine-technical-plan.md)
reservavam `LVFI-ENG-004` para o Método 2. O
[documento 29](../products/linha-de-valor-football-intelligence/29-lvfi-eng-004-total-market-numerical-stability.md)
e o Git registram o mesmo ID na correção numérica integrada pelo PR #4. O Product
Owner resolveu o conflito em 2026-08-02 pelas decisões `GOV-D-005/006`; os
documentos 11 e 13 foram corrigidos sem reescrever o histórico da correção.
As correções, o sistema de continuidade e os handoffs foram publicados e
integrados pelo PR #15 no merge
`a1610c85282e5d46ffc2b8094462d00d5135ca01`; a decisão `GOV-D-007` registra o
encerramento institucional da R21-GOV-001.

O [README do produto](../products/linha-de-valor-football-intelligence/README.md)
também declarava backend, banco e API ausentes apesar dos documentos 28–36 e dos
merges de APP-002 a APP-009. O Product Owner autorizou sua atualização factual.

## Decisões pendentes ou adiadas

| Tema | Estado | Responsável | Impacto | Fonte |
| --- | --- | --- | --- | --- |
| ID e plano do Método 2 | Pendente; deliberadamente adiada | Product Owner/CTO | Bloqueia nomear/iniciar a task | `GOV-D-006` |
| Escopo técnico da APP-011 | Pendente; etapa apenas planejada | Product Owner/CTO | Não bloqueia APP-010 | `GOV-D-004` |
| PDF-resumo: tecnologia, catálogo, retenção e marca | Pendente | Product Owner/CTO | MVP e relatórios | [UX/PDF](../products/linha-de-valor-football-intelligence/09-user-experience-and-pdf.md) |
| Autenticação, perfis e dados pessoais | Pendente por etapa | Product Owner/CTO | MVP, piloto e comercialização | [requisitos](../products/linha-de-valor-football-intelligence/05-requirements.md) |
| Deploy, backup, restauração e RPO/RTO | Pendente | Product Owner/CTO | Piloto e produção | ADRs 011–013 e requisitos |
| Provedores de dados/odds | Pendente | Product Owner/CTO | Ampliação analítica e mercado | [roadmap](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md) |
| Evento do Value Tracker e metodologia de CLV | Pendente | Product Owner/CTO | Integração futura | [Value Tracker](../products/linha-de-valor-football-intelligence/10-value-tracker-integration.md) |
| Critérios de piloto e cutover | Pendente | Product Owner | Piloto/comercialização | [roadmap](../products/linha-de-valor-football-intelligence/11-mvp-roadmap-and-validation.md) |
