# Arquitetura da aplicação LVFI

## Decisão

**DECISÃO APROVADA — LVFI-APP-001:** LVFI será um monólito modular: web Next.js/TypeScript, API FastAPI/Python, PostgreSQL, worker Python, armazenamento de objetos S3-compatível e deploy gerenciado de baixo custo. Web, API e worker evoluem coordenadamente; não há microsserviços, broker/cache distribuído ou fornecedor de nuvem fixado.

## Componentes e fronteiras

A web apresenta fluxos e chama API autorizada; não calcula nem acessa banco/segredos. A API orquestra casos de uso, autorização, transações e DTOs; o domínio LVFI contém futebol, importação, amostras, workflow, snapshots e relatórios; persistência contém repositórios; PostgreSQL contém dados, versões, auditoria e jobs; worker executa jobs idempotentes; adaptadores normalizam fornecedores; objetos guardam importações/PDFs; observabilidade mantém logs, métricas e health checks.

`packages/pricing-engine` permanece a única fonte matemática. API/worker chamam `run_method_one` localmente, a partir de dados normalizados, amostras materializadas e configuração resolvida; o motor não conhece HTTP, banco, fornecedor, PDF, usuário ou UI. Cada execução retém IDs estáveis, versão de dados, versões de distribuição/Engine/Método/catálogo/schema, configuração, `input_hash`, `configuration_hash`, `result_hash`, payload canônico autorizado, warnings e blockers. Metadados operacionais ficam separados. A web recebe DTOs por papel e nunca reimplementa cálculos.

## Dados e fluxos

LVFI é owner de entidades de futebol, importações, amostras, versões/configurações, execuções, snapshots, relatórios, odds e auditoria; Value Tracker será owner de aposta e resultado financeiro. IDs internos são estáveis; IDs externos são mappings. Dado bruto, normalizado e decisão de conciliação são separados; zero, ausência e inválido não se confundem. Importação aceita e aprovação são transacionais; snapshots aprovados são imutáveis, correções geram revisões e odds futuras são append-only.

`selecionar partida → histórico → amostras → configuração → run_method_one → persistir versões/hashes → revisão → snapshot`. Jobs de importação, geração preliminar, PDF e reprocessamento têm ID, correlação, tentativas limitadas e idempotency key. PDF vem somente de snapshot aprovado. Fornecedores futuros passam por adaptador/normalização/conciliação. Value Tracker usa evento/outbox versionado e idempotente, sem bloquear aprovação.

## Segurança e operação

A fundação preparará autenticação futura com papéis `admin`/`subscriber` e autorização no servidor; assinantes não recebem fórmulas, calibrações ou payload canônico completo. Segredos ficam fora do repositório, logs e cliente. Importações são limitadas, validadas sem executar macros e isoladas. Logs estruturados não carregam segredos; métricas cobrem API, cálculo, jobs, importação e PDF. PostgreSQL e objetos exigem backup e restauração ensaiada antes do piloto. Ambientes: local (dados sintéticos/sanitizados), teste, piloto e produção.

## Estrutura e sequência

Estrutura-alvo, sem criar scaffolding: `apps/web`, `apps/api`, `apps/worker`, `packages/pricing-engine` preservado, `packages/shared-contracts` somente com consumidor real, `infra` somente com decisão de deploy, além de docs/scripts/tests/fixtures.

Próximos marcos: **LVFI-APP-002 — Fundação do backend e banco**; importação histórica; execução persistida do Método 1; interface; mercado/oportunidades; relatórios, autenticação e piloto. Iniciar backend/banco exige Task aprovada com schema/migração/rollback, dados de teste, backup, contrato `run_method_one` preservando versões/hashes e definição de secrets, papéis, logs e auditoria.
