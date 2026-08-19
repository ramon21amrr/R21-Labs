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

Monólito modular: frontend Next.js/TypeScript, API FastAPI/Python; PostgreSQL;
worker Python e objetos S3-compatíveis futuros. `apps/web` fornece a primeira
interface utilizável; Pricing Engine e Método 1 permanecem isolados e são a única
fonte matemática. A aplicação já oferece dados históricos, amostras, execução,
persistência append-only, histórico, comparação e reprodução controlada.

- Referência: `449fde5e7279818c72a549b8c51d740ba45dc60d` em `main` / `origin/main`,
  integração do PR #18.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- API: baseline 86 testes e cobertura integral.
- Pricing Engine: 554 testes e cobertura integral.
- Última task institucional concluída: `R21-GOV-001`, publicada e integrada pelo
  PR #15 no merge `a1610c85282e5d46ffc2b8094462d00d5135ca01`.
- Última task de produto concluída: `LVFI-APP-010`, publicada pelo PR #17 no merge `2c2f34e7059c69d904250e4d0f5caa62ab36543d`.
- Task ativa: nenhuma.
- Próxima task oficial: `LVFI-ENG-006 — Camada versionada de precificação de mercados`;
  aprovada, ainda não implementada, base `449fde5e7279818c72a549b8c51d740ba45dc60d`.
- `LVFI-ENG-005` permanece Método 3 — frequência observada.
- `LVFI-APP-011` permanece planejada e bloqueada pela conclusão da ENG-006.

## Sequência macro

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

APP-010 inicia a interface utilizável. ENG-006 é a camada pós-Método 1 para
precificação por mercado com versionamento, snapshot, hashes e auditoria próprios,
sem alterar a matemática. APP-011 só poderá seguir após a ENG-006. O MVP ainda exige capacidades aprovadas nos documentos de produto,
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

**Ação imediata:** aguardar autorização própria para iniciar a ENG-006. Ela recebe
taxas imutáveis do Método 1 e usa capacidades existentes do Engine; Método 1
`1.0.0`, Pricing Engine e sua matemática permanecem congelados. A APP-011 segue
planejada/bloqueada, sem detalhamento adicional.

APP-010 está encerrada institucionalmente; ENG-006 está aprovada e ainda não
implementada; APP-011 não foi iniciada. O roadmap completo permanece em
[roadmap institucional](lvfi-product-roadmap.md), inclusive MVP, piloto,
operação de mercado, oportunidades, Value Tracker, preparação comercial e
lançamento.
