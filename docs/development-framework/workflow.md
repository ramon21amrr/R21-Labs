# Workflow de Desenvolvimento

## Como nasce o trabalho

### Initiative

Uma Initiative nasce de um objetivo amplo definido pelo Product Owner. Ela registra o resultado desejado e pode ser dividida em vários Sprints.

### Sprint

Um Sprint nasce quando uma parte da Initiative pode ser expressa como um objetivo pequeno e verificável. Deve conter entregáveis, Tasks, limites, dependências, riscos e critérios de aceitação.

Estados oficiais:

`Proposto → Em análise → Aprovado → Em execução → Em revisão → Concluído`

Estados excepcionais:

- **Bloqueado:** existe um impedimento identificado.
- **Cancelado:** o objetivo perdeu validade por decisão explícita.

### Task

Uma Task nasce da divisão de um Sprint em uma unidade implementável e revisável. Deve possuir objetivo, contexto, escopo, critérios de aceitação, dependências e resultado esperado.

## Fluxo de uma Task

1. O CTO especifica a Task.
2. O Software Engineer analisa a especificação e o estado atual do repositório.
3. O Software Engineer apresenta um plano de implementação.
4. O responsável aprova o plano ou solicita ajustes.
5. O Software Engineer implementa somente o plano aprovado.
6. O Software Engineer realiza as validações aplicáveis.
7. O Software Engineer apresenta o resumo da entrega.
8. A revisão aceita o resultado ou solicita correções.
9. A alteração aprovada é registrada no Git e enviada ao GitHub conforme o fluxo vigente.

## Regras de aprovação

- Aprovação deve ser explícita e indicar o plano, Sprint ou decisão autorizada.
- Aprovar um objetivo não autoriza automaticamente modificar arquivos.
- Aprovar um Sprint só autoriza as Tasks cujos planos estejam incluídos ou aprovados separadamente.
- Mudanças materiais de escopo, comportamento ou arquitetura invalidam a aprovação da parte afetada.
- O trabalho deve parar e voltar para análise quando a execução exigir decisão estratégica não aprovada.

## Correções e novas demandas

- Defeitos encontrados durante a revisão pertencem à mesma Task quando impedem seus critérios de aceitação.
- Uma funcionalidade adicional deve se tornar uma nova Task.
- Uma correção emergencial pode ocorrer fora do Sprint planejado, mas continua exigindo contexto, aprovação, validação e registro.

## Bloqueios e cancelamentos

Um bloqueio deve registrar o impedimento, seu impacto e o que é necessário para continuar. Um cancelamento deve registrar a decisão e preservar o histórico do trabalho já realizado.

## Conclusão

Uma Task ou Sprint só pode ser concluído quando atender à [definição de pronto](quality.md) correspondente e receber a revisão prevista.
