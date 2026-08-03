# Handoff de sessão do LVFI

## Identidade e objetivo

R21 Labs é uma software house de produtos próprios que transforma conhecimento em
software. O LVFI é seu primeiro produto: plataforma web auditável para dados de
futebol, amostras, modelos, probabilidades, odds justas, linhas, comparação e
relatórios. O Product Owner é Ramon, usuário inicial e autoridade final, e prefere
uma ação simples por vez, com evidência e sem decisões técnicas implícitas.

## Regras de orientação

Git e documentos versionados são a memória oficial. Comece por
[current-state](lvfi-current-state.md), valide
[project-state](lvfi-project-state.yaml) e consulte o
[task registry](lvfi-task-registry.md). Não infira a próxima task, não replaneje o
produto, não altere uma decisão aprovada e pare diante de conflito. Use Graphify
como mapa local, confirme nos originais e mantenha saídas compactas.

## Arquitetura e estado técnico

Monólito modular: frontend previsto em Next.js/TypeScript; API FastAPI/Python;
PostgreSQL; worker Python e objetos S3-compatíveis futuros. Hoje `apps/api` existe;
`apps/web` ainda não. Pricing Engine e Método 1 permanecem isolados e são a única
fonte matemática. A aplicação já oferece dados históricos, amostras, execução,
persistência append-only, histórico, comparação e reprodução controlada.

- Referência: `094b9ea51d6dabbac6154ec66e987d5fe83d8033` em `main`.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- API: baseline 86 testes e cobertura integral.
- Pricing Engine: 554 testes e cobertura integral.
- Última task concluída: `LVFI-APP-009`.
- Task institucional atual: `R21-GOV-001`, até sua integração.
- Próxima task oficial: `LVFI-APP-010`.
- Próxima etapa planejada: `LVFI-APP-011`.

## Sequência macro

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

APP-010 inicia a interface utilizável. APP-011 prepara entrada/comparação de
mercado. O MVP ainda exige capacidades aprovadas nos documentos de produto,
incluindo Métodos restantes, autenticação, workflow de aprovação, Match Center e
PDF. Mercado automatizado, oportunidades e Value Tracker permanecem fora do MVP
ou futuros conforme o [roadmap](lvfi-product-roadmap.md).

## Fluxo ChatGPT/OpenCode/Codex e Git

ChatGPT/CTO organiza requisitos e decisões; OpenCode/Codex implementam somente
task e plano aprovados; Product Owner decide e aceita. Confirme baseline e branch
não-main; implemente escopo mínimo; rode gates; revise diff/segredos; atualize a
continuidade; só então solicite commit. Push, PR e merge são ações separadas e
explícitas. Nunca force-push, reescreva histórico ou publique em `main`.

## Fontes e ação imediata

Leia [Company Context](../company/company-context.md),
[Framework](../development-framework/README.md),
[índice do produto](../products/linha-de-valor-football-intelligence/README.md),
[arquitetura](../products/linha-de-valor-football-intelligence/27-application-architecture.md)
e [reprodução](../products/linha-de-valor-football-intelligence/36-controlled-pricing-execution-reproduction.md)
quando a próxima task exigir. Gates são proporcionais ao escopo e mantêm logs em
`.r21-artifacts/quality/`.

**Ação imediata:** após integrar R21-GOV-001, executar somente
`LVFI-APP-010 — Fundação do frontend e tela inicial de precificação`.
