# LVFI — handoff único para novo chat

## Estado verificável

- Produto: plataforma auditável de dados, análise e precificação de futebol.
- Product Owner e usuário inicial: Ramon.
- Base estável histórica da última task: `0b012291e78fb3b20eb887964ebc26d170e0a81c`.
  Não representa o SHA corrente.
- Estado corrente: resolver com `git rev-parse HEAD`, `git rev-parse main` e
  `git rev-parse origin/main`; SHAs textuais são apenas evidência histórica.
- Última task de produto concluída: `LVFI-ENG-005`, PR #33.
- Última task institucional concluída: `R21-GOV-003`, PR #36 e merge histórico
  `c9726fae50bb3b355800e83d1ad9fb8f77216536`.
- Task ativa: `LVFI-ENG-007 — Método 2 — Poisson ajustado`, implementada e
  pronta para publicação, sem autorização de publicação nesta sessão.
- Estado: adaptador interno APP-013, evidência auditável, predicado canônico de
  concluída e complementos reais foram validados; Método 1, Método 3 e Pricing
  Engine permanecem preservados.
- Próxima ação: aguardar autorização explícita de publicação; não iniciar task
  sucessora.

Capacidades atuais: FastAPI/PostgreSQL, importação histórica revisada e
idempotente, partidas futuras, revisões estatísticas append-only, consultas,
amostras, camada estatística comum configurável, Método 1, execuções append-only,
histórico, comparação, reprodução,
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
Value Tracker permanecem fora da primeira versão. Método 2 é `LVFI-ENG-007`,
implementado como `method_two_adjusted_poisson` `1.0.0`, com schemas 1 e
evidência SHA-256; sua publicação ainda requer autorização explícita.
`LVFI-ENG-005` é Método 3 e está encerrada institucionalmente. Os arquivos privados não
estão no Git; seus fingerprints estão no documento 39. A revisão corrigida do
XLSM termina em `D45D3924` e suas 2.694 linhas passaram na revalidação estrutural.

## Regras para continuar

1. Leia [estado](lvfi-current-state.md),
   [YAML](lvfi-project-state.yaml), [tasks](lvfi-task-registry.md) e
   [decisões](lvfi-decision-register.md).
2. Confirme branch e árvore; leia `reference_commit` como base aprovada e
   resolva HEAD, main e origin/main no runtime com `git rev-parse`.
3. Use Graphify-first; o grafo foi reconstruído em 2026-09-07 no modo local
   `code-only` (316 nós/663 relações), mas continua sendo apenas um índice.
4. Nunca modifique Método 1, schemas, hashes, fixtures ou contratos para esconder
   divergência.
5. Não publique nem inicie task sucessora sem nova autorização explícita.

## Ação única

Aguardar autorização explícita de publicação da `LVFI-ENG-007`.

## Bootstrap

```text
Trate Git e este handoff como fontes de verdade. Valide current-state, YAML e
registry; trate reference_commit como base estável e resolva o estado corrente
por git rev-parse. Não infira próxima task. Preserve Método 1 e o Pricing
Engine. Use Graphify como índice e confirme decisões nas fontes originais.
Apresente uma ação por vez em linguagem simples.
```
