# Checklist de encerramento de task LVFI

Nenhuma task futura é encerrada institucionalmente sem completar este checklist.

## 1. Encerramento técnico

- [ ] Implementação e documentação técnica concluídas no escopo aprovado.
- [ ] Gates aplicáveis executados e evidências/logs registrados.
- [ ] Diff revisado; produto, contratos, schemas, hashes, versões e matemática
      preservados ou alterados somente com autorização específica.
- [ ] `git diff --check` e varredura de segredos aprovados.
- [ ] Recursos temporários removidos com segurança.

## 2. Publicação

- [ ] Commit coerente e autorizado criado na branch da task.
- [ ] Push da branch autorizado e concluído.
- [ ] PR criado, revisado e checks aprovados.
- [ ] Merge autorizado e concluído.
- [ ] `main` sincronizada por fast-forward; ahead/behind `0/0`.
- [ ] Working tree limpa.

Publicação nunca é inferida. Durante revisão pré-commit, itens desta seção ficam
explicitamente pendentes.

## 3. Encerramento institucional

- [ ] [Task registry](lvfi-task-registry.md) atualizado com branch, commit, PR,
      merge, data, entrega e status.
- [ ] [Current state](lvfi-current-state.md) atualizado.
- [ ] [Project state YAML](lvfi-project-state.yaml) atualizado e validado.
- [ ] [Roadmap](lvfi-product-roadmap.md) e [marcos](lvfi-milestones.md) atualizados
      quando o produto ou a sequência forem afetados.
- [ ] [Decision register](lvfi-decision-register.md) atualizado quando aplicável.
- [ ] [Session handoff](lvfi-session-handoff.md) e
      [handoff único](LVFI-CHAT-HANDOFF.md) regenerados.
- [ ] Próxima task oficial ou próxima decisão definida pelo Product Owner.
- [ ] Ação imediata registrada sem inferência.
- [ ] Reference commit/branch atualizados para o merge integrado.
- [ ] Estado final apresentado ao Product Owner e aceito.

Encerramento técnico sem publicação é **tecnicamente pronto**. Merge sem controle
atualizado é **publicado, mas institucionalmente aberto**. Somente as três seções
concluídas tornam a task **institucionalmente encerrada**.
