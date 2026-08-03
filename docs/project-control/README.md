# Controle institucional do LVFI

## Finalidade

Esta área é a memória operacional versionada do Linha de Valor Football
Intelligence (LVFI). Toda informação necessária para continuidade deve existir no
Git. Conversas podem explicar e coordenar, mas nunca são a única fonte de roadmap,
estado, decisão, próxima task, dependência, restrição, aceite ou ação imediata.

## Ordem de leitura para retomada

1. [Estado atual](lvfi-current-state.md).
2. [Estado legível por máquina](lvfi-project-state.yaml).
3. [Registro de tasks](lvfi-task-registry.md).
4. [Registro de decisões](lvfi-decision-register.md).
5. [Roadmap](lvfi-product-roadmap.md) e [marcos](lvfi-milestones.md).
6. [Handoff de sessão](lvfi-session-handoff.md) ou o
   [handoff único](LVFI-CHAT-HANDOFF.md).
7. Documentos originais apontados por esses artefatos.

Para um novo chat, o caminho mínimo é anexar `LVFI-CHAT-HANDOFF.md`. O caminho
auditável é anexar `lvfi-session-handoff.md` e `lvfi-project-state.yaml`, então
usar o [bootstrap](lvfi-new-chat-bootstrap.md).

## Autoridade

Este controle não substitui suas fontes. A ordem aplicável é:

1. [Company Context](../company/company-context.md);
2. [R21 Development Framework](../development-framework/README.md);
3. esta área de controle;
4. [documentação do produto](../products/linha-de-valor-football-intelligence/README.md);
5. roadmap, arquitetura, ADRs, documentos técnicos, histórico Git, código e testes.

Decisão explícita mais recente do Product Owner prevalece para o caso decidido.
Conflito material deve ser registrado e levado ao Product Owner; nenhum agente
pode resolvê-lo por inferência.

## Processo de atualização

No início de toda task LVFI, validar `current-state`, YAML, task registry, SHA e
próxima task oficial antes de criar a branch. No encerramento institucional,
atualizar pelo menos estado atual, YAML, registry, handoff e ação imediata; roadmap
e decisões são atualizados quando afetados. Use o
[checklist de encerramento](lvfi-task-closure-checklist.md) e o
[workflow de continuidade](lvfi-continuity-workflow.md).

Nenhuma task futura é considerada encerrada institucionalmente enquanto esses
artefatos obrigatórios permanecerem desatualizados.

## Responsabilidades

- **Product Owner:** define prioridade, aprova decisões e conflitos, aceita a
  entrega e autoriza publicação.
- **Agentes:** verificam o estado no Git, não inferem a próxima task, consultam
  Graphify-first para localização, confirmam decisões nos originais, mantêm
  saídas compactas e atualizam a continuidade dentro da task aprovada.

O Company Context fornece identidade e autoridade; o Framework fornece o processo;
o roadmap do produto fornece o destino. Esta área liga os três ao estado executável
do repositório.

## Artefatos

- [Roadmap do produto](lvfi-product-roadmap.md)
- [Mapa de marcos](lvfi-milestones.md)
- [Registro de tasks](lvfi-task-registry.md)
- [Estado atual](lvfi-current-state.md)
- [Estado YAML](lvfi-project-state.yaml)
- [Registro de decisões](lvfi-decision-register.md)
- [Handoff de sessão](lvfi-session-handoff.md)
- [Bootstrap para novos chats](lvfi-new-chat-bootstrap.md)
- [Checklist de encerramento](lvfi-task-closure-checklist.md)
- [Workflow de continuidade](lvfi-continuity-workflow.md)
- [Handoff único](LVFI-CHAT-HANDOFF.md)
