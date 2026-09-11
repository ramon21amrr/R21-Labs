# LVFI-APP-017 — Autenticação Local de Administrador

## Contrato aprovado

Esta task adiciona autenticação exclusivamente local para o usuário único
`admin`. Não cria múltiplos usuários, papéis adicionais, OAuth/SSO, publicação
remota ou qualquer capacidade de task posterior.

- Bootstrap e recuperação ocorrem somente pelo CLI local, com entrada oculta e
  confirmação; a senha não é aceita por argumento, código, Git ou log.
- Somente hash Argon2id da senha é persistido. A senha aceita de 12 a 128
  caracteres; cinco falhas bloqueiam o login por 15 minutos e a resposta não
  distingue credencial incorreta de bloqueio.
- A sessão usa token opaco de alta entropia, do qual somente SHA-256 é
  persistido. O cookie é `HttpOnly`, `SameSite=Strict` e recebe `Secure` quando
  o transporte público usa HTTPS. Em um frontend HTTPS com rewrite interno HTTP,
  o operador configura `LVFI_EXTERNAL_HTTPS=true`; o hop interno não decide essa
  propriedade de segurança.
- A sessão expira por 30 minutos de inatividade ou 12 horas absolutas. A
  atividade renova apenas o limite de inatividade; logout invalida
  imediatamente.
- A troca de senha exige a senha atual e invalida as demais sessões. O reset
  administrativo local invalida todas as sessões. Não há e-mail, pergunta
  secreta ou fluxo “esqueci minha senha” no MVP.
- Toda rota de negócio da API é autorizada no servidor. O `actor` de novas
  operações auditáveis é derivado da sessão autenticada, nunca de payload do
  frontend. A UI possui guarda server-side complementar; ela não substitui a
  autorização da API.

## Persistência e compatibilidade

A migration `20260911_10` é aditiva sobre `20260910_09`: credencial singleton,
sessões revogáveis e ledger de eventos de autenticação append-only. Os contratos
e ledgers de APP-012 a APP-016, o Pricing Engine e Métodos 1/2/3 não foram
alterados. O rollback remove somente os objetos APP-017.

## Operação local

Após aplicar as migrations, o Product Owner executa `python -m lvfi_api.cli
admin-bootstrap` para criar a credencial e `admin-reset-password` apenas para
recuperação local. Ambos solicitam a senha duas vezes por entrada oculta.

## Publicação e encerramento

O commit técnico `af2bfb93893abfe878ce7e106b7a482657f7caba` foi publicado no PR #46
e integrado por merge commit `32c2cbd267deea449f9c572fbdc85f56d442b4b0`.
Os gates de API, PostgreSQL 16 isolado, frontend e Pricing Engine passaram; QA e
revisão de segurança não deixaram P0/P1 abertos. Para HTTPS com rewrite interno,
`LVFI_EXTERNAL_HTTPS=true` é requisito operacional. Cobertura dedicada de
`proxy.ts` permanece melhoria P2 futura, sem bloquear esta entrega.
