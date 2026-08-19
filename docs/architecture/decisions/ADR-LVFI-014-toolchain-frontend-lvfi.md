# ADR-LVFI-014 — Toolchain do frontend LVFI

## Status

Aprovada, com emenda de compatibilidade em 2026-08-19

## Contexto

A `LVFI-APP-010` materializa pela primeira vez o frontend previsto na ADR-LVFI-011.
A implementação requer versões reprodutíveis do runtime, framework, testes e
lint, sem antecipar ferramentas fora do escopo da interface inicial.

## Decisão

O Product Owner aprovou, em 2026-08-19, a matriz inicial para `apps/web`:

- Node.js `24.19.0` LTS e npm `11.17.0`, exclusivamente;
- Next.js `16.3.1`, com App Router;
- React e React DOM `19.2.7`;
- TypeScript `5.9.3`;
- ESLint `10.8.1` e `eslint-config-next` `16.3.1`, com Flat Config;
- Vitest `4.1.10`, `@testing-library/react` `16.3.2`,
  `@testing-library/user-event` `14.6.4` e jsdom `30.0.1`;
- Playwright `1.60.0` somente quando necessário para smoke ou E2E.

As dependências diretas terão versões exatas e o `package-lock.json` será
versionado. Tipos auxiliares compatíveis com Node 24 e React 19 serão resolvidos e
congelados pelo lockfile. Não serão usados pnpm, Yarn, Bun, versões canary, beta,
RC, React Compiler, TypeScript 6/7 ou ferramentas adicionais sem necessidade
demonstrada nesta task.

Na validação, `eslint-config-next` `16.3.1` trouxe plugins transitivos cujo peer
support termina no ESLint 9. Com ESLint `10.8.1`, o lint falhou antes de analisar
o código por incompatibilidade de API. Após a autorização do Product Owner para
continuar, a versão direta efetiva foi emendada para ESLint `9.39.5`, estável,
compatível e fixada no `package-lock.json`. O Flat Config permanece usado, sem
React Compiler nem ferramentas adicionais.

## Consequências

O frontend terá instalação e validações reprodutíveis com npm, mantendo a
superfície de dependências limitada ao fluxo da APP-010. A emenda elimina o
bloqueio técnico do lint; a atualização para ESLint 10 somente poderá ocorrer
quando a cadeia transitiva do `eslint-config-next` declarar suporte compatível.

## Referências

- [ADR-LVFI-011](ADR-LVFI-011-stack-e-monolito-modular-da-aplicacao.md)
- `LVFI-APP-010` — decisão do Product Owner de 2026-08-19
