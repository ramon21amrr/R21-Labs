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
persistência append-only, histórico, comparação, reprodução controlada e a camada
local ENG-006 de snapshots teóricos de mercado.

- Baseline ENG-006: `bde1a362801658543ad9b2c3c9085aa10f0fcd04`; branch local
  `codex/lvfi-eng-006-market-pricing`, sem commit/push/PR/merge.
- Pricing Engine `1.0.1`; distribuição `1.1.1`; Método 1 `1.0.0`; schema 1.
- API: 96 testes no PostgreSQL institucional isolado e cobertura integral; banco
  descartável removido ao final.
- Pricing Engine: 554 testes e cobertura integral.
- Última task institucional concluída: `R21-GOV-001`, publicada e integrada pelo
  PR #15 no merge `a1610c85282e5d46ffc2b8094462d00d5135ca01`.
- Última task de produto concluída: `LVFI-APP-010`, publicada pelo PR #17 no merge `2c2f34e7059c69d904250e4d0f5caa62ab36543d`.
- Task ativa: `LVFI-ENG-006`, implementada e tecnicamente pronta, aguardando
  revisão/autorização de commit do Product Owner.
- Próxima decisão: autorizar ou rejeitar o commit da ENG-006; não iniciar nova task.
- `LVFI-ENG-005` permanece Método 3 — frequência observada.
- `LVFI-APP-011` permanece planejada e bloqueada pela conclusão da ENG-006.

## Sequência macro

`dados → modelo → preço → mercado → oportunidade → resultado → melhoria contínua`

APP-010 inicia a interface utilizável. A ENG-006 local recebe taxas imutáveis,
chama apenas APIs públicas do Engine e persiste snapshots de mercados com schema,
serialização canônica, SHA-256 e trigger append-only. Preserva linhas/estados
asiáticos e não altera matemática. APP-011 só poderá seguir após o encerramento
da ENG-006. O MVP ainda exige capacidades aprovadas nos documentos de produto,
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

**Ação imediata:** Product Owner revisar a ENG-006 e autorizar ou rejeitar o
commit. Método 1 `1.0.0`, Pricing Engine `1.0.1` e sua matemática permanecem
congelados. A APP-011 segue planejada/bloqueada e não foi alterada.

APP-010 está encerrada institucionalmente; ENG-006 está tecnicamente pronta, mas
não publicada nem institucionalmente encerrada; APP-011 não foi iniciada. O
roadmap completo permanece em
[roadmap institucional](lvfi-product-roadmap.md), inclusive MVP, piloto,
operação de mercado, oportunidades, Value Tracker, preparação comercial e
lançamento.
