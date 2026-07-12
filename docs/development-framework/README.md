# R21 Development Framework

## Objetivo

O R21 Development Framework é o método oficial para transformar uma ideia em software revisado, documentado e versionado. Ele se aplica a todos os produtos da R21 Labs e não depende de linguagem, framework ou infraestrutura.

Sua regra central é:

> Nenhuma mudança entra em um produto sem objetivo, plano, aprovação, implementação, validação e registro.

## Princípios

- Primeiro construímos o processo; depois construímos os produtos.
- Nenhuma implementação começa sem aprovação.
- Tecnologias são escolhidas somente na fase de arquitetura.
- Simplicidade e evolução incremental têm preferência.
- Complexidade precisa responder a uma necessidade comprovada.
- Decisões importantes devem ser compreensíveis e registradas.
- A IA integra a equipe, mas não possui autorização implícita.

## Papéis e responsabilidades

### Product Owner — humano

- Define problemas, objetivos e prioridades.
- Explica o valor esperado para o negócio e para o usuário.
- Aprova escopo e critérios de sucesso.
- Decide o que entra ou não em cada Sprint.
- Aceita ou rejeita o resultado entregue.

### CTO — ChatGPT

- Transforma objetivos em requisitos e prioridades.
- Define a arquitetura na fase apropriada.
- Prepara especificações e critérios de aceitação.
- Divide iniciativas em Sprints e Tasks.
- Registra riscos e decisões estratégicas.
- Verifica a coerência das soluções entre produtos.

### Software Engineer — Codex

- Analisa a especificação e o repositório.
- Identifica dúvidas, riscos, dependências e impactos.
- Propõe um plano antes de alterar arquivos.
- Implementa somente o que foi aprovado.
- Valida o resultado e atualiza a documentação afetada.
- Apresenta um resumo para revisão.

### Revisão

- Confirma o atendimento aos critérios de aceitação.
- Verifica qualidade, segurança e aderência ao escopo.
- Aceita a entrega ou solicita correções.

## Hierarquia do trabalho

1. **Produto:** software mantido pela R21 Labs.
2. **Initiative:** objetivo amplo que pode exigir vários Sprints.
3. **Sprint:** ciclo pequeno com objetivo e resultado verificável.
4. **Task:** unidade implementável e revisável.
5. **Commit:** registro técnico coerente de parte concluída.
6. **Release:** versão disponibilizada em um ambiente definido.

## Ciclo de vida de um produto

1. **Proposta:** problema, público, valor esperado e responsável.
2. **Descoberta:** requisitos, jornadas, regras e escopo inicial.
3. **Arquitetura:** tecnologias, componentes, dados, segurança e operação.
4. **Planejamento:** Sprints, Tasks, dependências e critérios de aceitação.
5. **Implementação:** desenvolvimento incremental após aprovação.
6. **Validação:** verificações técnicas e aceite do Product Owner.
7. **Release:** versionamento, publicação e registro.
8. **Operação:** monitoramento, suporte, correções e evolução.

## Aprovações obrigatórias

- **Produto:** autoriza iniciar a descoberta.
- **Arquitetura:** autoriza usar a solução técnica definida.
- **Sprint:** autoriza trabalhar no conjunto aprovado de Tasks.
- **Plano da Task:** autoriza modificar os arquivos definidos no plano.

A aprovação deve ser explícita e vinculada ao objeto aprovado. Uma mudança material de escopo ou arquitetura exige nova aprovação da parte afetada.

## Documentos do framework

- [Workflow](workflow.md): nascimento e andamento de Sprints e Tasks.
- [Colaboração com IA](ai-collaboration.md): responsabilidades e limites dos agentes.
- [Git e GitHub](git-github.md): branches, commits, push e revisão.
- [Qualidade](quality.md): critérios de revisão e definição de pronto.
- [Templates](templates/): modelos oficiais para execução do processo.

## Evolução do framework

O framework evolui de forma incremental. Toda mudança deve possuir motivo, proposta e aprovação. Novas regras só devem ser adicionadas quando uma necessidade real for observada; processos que não agreguem qualidade ou previsibilidade devem ser simplificados.
