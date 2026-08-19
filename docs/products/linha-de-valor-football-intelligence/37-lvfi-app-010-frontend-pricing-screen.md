# LVFI-APP-010 — Fundação do frontend e tela inicial de precificação

## Objetivo

`apps/web` introduz a primeira interface web operacional do LVFI. Ela permite localizar uma partida histórica, consultar as amostras públicas do Método 1, criar uma execução persistida e consultar o resultado canônico ou um registro já persistido. A interface está em português do Brasil e prioriza desktop, sem impedir uso em telas menores.

## Arquitetura

O frontend é um aplicativo Next.js `16.3.1` com App Router e TypeScript. A matriz reprodutível completa está na [ADR-LVFI-014](../../architecture/decisions/ADR-LVFI-014-toolchain-frontend-lvfi.md). O npm é o único package manager e o `package-lock.json` congela a resolução.

A URL do servidor da API é centralizada em `LVFI_API_URL`; quando ela não é definida no ambiente de desenvolvimento, o rewrite do Next aponta `/api` para `http://127.0.0.1:8000`. O navegador usa o caminho same-origin `/api`, sem exigir CORS da API. `NEXT_PUBLIC_LVFI_API_URL` permite uma substituição pública explícita quando o ambiente já oferece CORS. O cliente HTTP tipado concentra requests e converte apenas falhas HTTP em mensagens sanitizadas. Nenhuma estrutura interna, stack trace, segredo, ORM ou consulta SQL é exposta pela web.

## Rotas e fluxo

- `/` lista `GET /matches`, com paginação e os filtros públicos `team_id`, `date_from` e `date_to`.
- `/matches/[matchId]` consulta `GET /matches/{match_id}`, `GET /matches/{match_id}/method-one/sample` e o histórico `GET /matches/{match_id}/method-one/pricing-executions`.
- A ação de precificação chama somente `POST /matches/{match_id}/method-one/pricing-executions`, com uma chave de idempotência nova por tentativa deliberada.
- Abertura de histórico chama somente `GET /pricing-executions/{execution_id}`.

O frontend mostra identidade pública da partida, completude e quantidade de observações de cada amostra, warnings, bloqueios, estados de carregamento e de falha, `execution_id`, timestamps, correlation ID, versões e fingerprints públicos. A qualidade não é recomputada: o contrato de amostra atual fornece completude e warnings; outros indicadores só são apresentados quando a API os publicar.

O resultado retorna pela execução persistida e é renderizado recursivamente com os valores literais recebidos. Não há cálculo, alteração de precisão, fórmula, probabilidade, odd, linha, mercado, comparação de mercado ou regra do Pricing Engine no navegador.

## Testes e limites

A suíte Vitest cobre listagem, filtros, paginação, vazio, erro sanitizado, amostra completa e bloqueada, warnings, execução concluída e bloqueada, resultado canônico e abertura de execução persistida. Typecheck e build de produção são scripts locais do `apps/web`.

Na validação da matriz inicial, os plugins transitivos de `eslint-config-next`
`16.3.1` declararam suporte até ESLint 9 e falharam com ESLint `10.8.1`. Com a
autorização do Product Owner para continuar, ESLint `9.39.5` foi fixado como a
versão estável compatível; o mesmo Flat Config passou limpo, sem excluir regras.
O lockfile registra integralmente essa resolução.

## Fora do escopo preservado

APP-010 não adiciona entrada ou comparação de mercado, EV, recomendação, aposta, Value Tracker, autenticação, PDF, deploy, ingestão, odds automáticas, Métodos 2/3, novos modelos ou qualquer fluxo da APP-011.
