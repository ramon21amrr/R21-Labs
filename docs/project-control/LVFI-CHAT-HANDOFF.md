# LVFI — handoff único para novo chat

## Estado verificável

- Produto: plataforma auditável de dados, análise e precificação de futebol.
- Product Owner e usuário inicial: Ramon.
- `main` / `origin/main`: `88d7ab486f007d946a053adba4a8ab552b78ee35`,
  merge do PR #26.
- Última task de produto concluída: `LVFI-APP-012`, PR #26.
- Última task institucional concluída: `R21-GOV-002`.
- Task ativa: nenhuma.
- Estado: `LVFI-APP-012` concluída, publicada, integrada e encerrada
  institucionalmente pelo PR #26.
- Próxima task sucessora: nenhuma; não inferir ID ou autorização.

Capacidades atuais: FastAPI/PostgreSQL, importação histórica revisada e
idempotente, partidas futuras, revisões estatísticas append-only, consultas,
amostras, Método 1, execuções append-only, histórico, comparação, reprodução,
snapshots teóricos de mercado, referência externa manual e interfaces iniciais.
Pricing Engine `1.0.1`, distribuição `1.1.1`, Método 1 `1.0.0` e schema 1
permanecem congelados.

## Decisão de 2026-09-06

O Product Owner aprovou o
[plano mestre](../products/linha-de-valor-football-intelligence/39-lvfi-master-plan-rebaseline.md):
primeira versão local para um administrador; entrada revisada por Excel/CSV e web;
sete grupos estatísticos por time; Métodos 1, 2 e 3 separados; configuração,
aprovação e snapshots; Match Center; PDF-resumo; launcher e recuperação.

Jogadores, membros, publicação remota, fornecedores automáticos, oportunidades e
Value Tracker permanecem fora da primeira versão. Método 2 não possui ID.
`LVFI-ENG-005` permanece Método 3 e não está autorizada. Os arquivos privados não
estão no Git; seus fingerprints estão no documento 39. A revisão corrigida do
XLSM termina em `D45D3924` e suas 2.694 linhas passaram na revalidação estrutural.

## Regras para continuar

1. Leia [estado](lvfi-current-state.md),
   [YAML](lvfi-project-state.yaml), [tasks](lvfi-task-registry.md) e
   [decisões](lvfi-decision-register.md).
2. Confirme branch, HEAD, origin/main e árvore antes de agir.
3. Use Graphify-first; o grafo foi reconstruído em 2026-09-06 no modo local
   `code-only`, mas continua sendo apenas um índice.
4. Nunca modifique Método 1, schemas, hashes, fixtures ou contratos para esconder
   divergência.
5. Execute uma task por vez e publique somente com autorização explícita.

## Ação única

O Product Owner deve nomear e autorizar uma única task posterior. Não inferir
seu ID, escopo ou autorização.

## Bootstrap

```text
Trate Git e este handoff como fontes de verdade. Valide current-state, YAML,
registry, branch e reference_commit. Não infira próxima task. Preserve Método 1
e o Pricing Engine. Use Graphify como índice e confirme decisões nas fontes
originais. Apresente uma ação por vez em linguagem simples.
```
