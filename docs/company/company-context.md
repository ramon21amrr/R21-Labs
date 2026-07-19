# Contexto Institucional da R21 Labs

## 1. Finalidade deste documento

Este documento é a principal fonte de contexto institucional da R21 Labs. Ele registra a identidade, os objetivos, os princípios e a forma de trabalho da empresa para orientar o fundador, agentes de inteligência artificial, desenvolvedores e futuros colaboradores.

Seu propósito é preservar coerência ao longo do tempo. Decisões sobre produtos, processos, arquitetura e tecnologia devem ser interpretadas à luz deste contexto.

Este documento não substitui especificações de produto, decisões arquiteturais, planos de Sprint ou procedimentos técnicos. Ele estabelece os fundamentos que orientam esses artefatos.

## 2. Identidade da empresa

A R21 Labs é uma software house fundada por Ramon de Oliveira Pereira para desenvolver e manter produtos digitais próprios. A prestação de serviços não constitui seu objetivo principal.

A empresa foi concebida para permitir que uma estrutura inicialmente composta por uma única pessoa desenvolva produtos profissionais com apoio intensivo de inteligência artificial, sem abrir mão de organização, qualidade, rastreabilidade e sustentabilidade.

O fundador não possui experiência profissional prévia em desenvolvimento de software e está construindo conhecimento em programação, arquitetura e engenharia de software durante a evolução da empresa. Essa condição não reduz o padrão de qualidade pretendido; ela torna essenciais processos explícitos, documentação útil, validação sistemática e limites claros para a autonomia da IA.

## 3. Missão

Transformar conhecimento em produtos digitais.

O software é uma forma de aplicar e distribuir conhecimento. O principal patrimônio intelectual da R21 Labs é o conhecimento que ela produz, organiza, valida e aperfeiçoa.

## 4. Visão

Construir um ecossistema de softwares próprios que compartilhem conhecimento, componentes e processos.

Cada produto deve resolver um problema definido e, sempre que houver benefício comprovado, fortalecer a capacidade da empresa de criar e evoluir outros produtos. O crescimento do ecossistema deve preservar a independência entre domínios e evitar dependências artificiais.

## 5. Princípios permanentes

A R21 Labs prioriza:

- **Simplicidade:** escolher a solução menos complexa que atenda corretamente à necessidade.
- **Organização:** manter responsabilidades, artefatos e decisões em locais claros.
- **Documentação útil:** registrar informações que apoiem entendimento, decisão, operação ou continuidade.
- **Evolução incremental:** produzir avanços pequenos, verificáveis e reversíveis sempre que possível.
- **Qualidade:** validar cada entrega de forma proporcional ao seu impacto e risco.
- **Reutilização consciente:** reutilizar conhecimento e componentes quando houver uso real, sem generalização prematura.
- **Baixo acoplamento:** preservar a capacidade de produtos e domínios evoluírem com independência.
- **Clareza:** tornar objetivos, limites, decisões e resultados compreensíveis.

Esses princípios implicam que a empresa não deve:

- criar complexidade para necessidades hipotéticas;
- criar estruturas sem uso real;
- desenvolver funcionalidades sem objetivo claramente definido;
- adotar abstrações antes de existir um caso concreto de uso;
- instalar ferramentas ou escolher frameworks antes de sua necessidade ser demonstrada;
- permitir que velocidade aparente substitua revisão e validação.

## 6. Modelo operacional

A inteligência artificial faz parte da equipe da R21 Labs. Sua participação ocorre dentro de papéis definidos, com autoridade limitada e revisão compatível com o impacto de cada decisão.

### 6.1 Product Owner — humano

Responsável por:

- definir a visão do negócio;
- estabelecer objetivos e prioridades;
- tomar decisões finais de produto e empresa;
- aprovar escopos, planos e entregas;
- aceitar ou rejeitar resultados.

### 6.2 CTO — ChatGPT

Responsável por:

- definir e proteger a coerência arquitetural;
- organizar requisitos, prioridades e trabalho técnico;
- revisar propostas e resultados;
- preservar a consistência entre produtos;
- identificar riscos e proteger a qualidade;
- transformar objetivos do Product Owner em direcionamento técnico.

O CTO não substitui a decisão final do Product Owner e não deve ampliar objetivos sem aprovação.

### 6.3 Software Engineer — Codex

Responsável por:

- analisar o estado técnico do projeto;
- propor planos de implementação;
- implementar somente o escopo aprovado;
- produzir ou atualizar documentação técnica pertinente;
- executar testes e validações;
- apresentar o resultado para revisão.

O Software Engineer nunca deve alterar arquivos antes da aprovação do plano correspondente. Também não deve tomar decisões estratégicas, modificar arquitetura aprovada ou implementar melhorias não solicitadas.

### 6.4 Responsabilidade humana

Resultados produzidos por IA devem ser compreensíveis e verificáveis. A geração de um conteúdo não comprova sua correção. A autoridade final permanece humana, e o uso de IA não elimina a necessidade de revisão, evidência ou responsabilidade.

## 7. Processo oficial de desenvolvimento

Todo trabalho segue este fluxo:

1. **Objetivo:** definição do resultado pretendido e de sua motivação.
2. **Análise:** compreensão do contexto, do estado atual, dos limites e dos riscos.
3. **Plano:** descrição das alterações, da ordem de execução e das validações.
4. **Aprovação:** autorização explícita do escopo e do plano.
5. **Implementação:** execução restrita ao que foi aprovado.
6. **Revisão:** verificação técnica e funcional do resultado.
7. **Aceite:** confirmação de que a entrega atende ao objetivo.
8. **Commit:** registro coerente da alteração aceita no histórico local.
9. **Push:** envio do histórico aprovado ao repositório remoto.

Nenhuma etapa pode ser ignorada. Uma alteração material no escopo ou no plano exige nova análise e nova aprovação antes da continuidade.

O detalhamento operacional desse processo pertence ao R21 Development Framework.

## 8. Desenvolvimento por Sprints

Toda evolução planejada ocorre por Sprints. Cada Sprint deve possuir:

- objetivo;
- escopo;
- itens explicitamente excluídos quando houver risco de ambiguidade;
- critérios de aceitação;
- revisão;
- encerramento documentado.

Um Sprint não deve começar sem planejamento e aprovação. Funcionalidades fora do escopo devem ser registradas como trabalho futuro, não incorporadas informalmente à implementação em andamento.

## 9. Ordem das decisões

A R21 Labs decide na seguinte ordem:

1. **Processo:** como o trabalho será conduzido e controlado.
2. **Produto:** qual problema será resolvido, para quem e com qual resultado esperado.
3. **Arquitetura:** como as responsabilidades e os fluxos do produto serão organizados.
4. **Tecnologia:** quais ferramentas concretizam a arquitetura aprovada.

Essa ordem não deve ser invertida. Tecnologias somente podem ser escolhidas quando os requisitos relevantes do produto estiverem claros. Preferência pessoal, popularidade ou disponibilidade de uma ferramenta não constituem, isoladamente, justificativa arquitetural.

## 10. Conhecimento como patrimônio

A R21 Labs produz, organiza e aplica conhecimento. Entre seus ativos podem estar:

- pesquisas;
- modelos matemáticos e estatísticos;
- metodologias;
- regras de negócio;
- algoritmos;
- processos;
- experimentos;
- paperbets;
- calibrações;
- resultados e aprendizados.

Esses ativos pertencem à empresa e devem permanecer compreensíveis, rastreáveis e reutilizáveis quando apropriado. Produtos utilizam esse conhecimento, mas não devem ser tratados como seu único repositório ou sua única forma de preservação.

Nem todo experimento se torna conhecimento consolidado. Hipóteses, evidências, resultados negativos e conclusões devem ser distinguidos para evitar que suposições sejam reutilizadas como fatos.

## 11. Estrutura do ecossistema

O ecossistema é organizado conceitualmente em três níveis:

1. **Empresa:** princípios, processos e capacidades compartilhadas pela R21 Labs.
2. **Domínio:** área de conhecimento ou negócio com linguagem e problemas próprios.
3. **Produto:** software que resolve problemas definidos dentro de um domínio.

O primeiro domínio será **Football**. O primeiro produto oficial da R21 Labs será a **Linha de Valor Football Intelligence**, uma plataforma web de inteligência de futebol, estatísticas, análise de partidas, classificação de campeonatos, rankings, desempenho, modelos de precificação, probabilidades, odds justas, linhas projetadas, comparação futura com odds de mercado e relatórios em PDF.

Conceitualmente, a Linha de Valor Football Intelligence concentra dados, estatísticas, análise, precificação, probabilidades, odds justas, linhas e identificação de oportunidades. O **Value Tracker** será desenvolvido posteriormente como outro produto ou módulo do ecossistema, concentrando o registro de oportunidades e apostas, resultados, unidades, lucro, ROI, yield, CLV, performance por modelo, performance por versão e auditoria operacional.

O Value Tracker será futuramente integrado à Linha de Valor Football Intelligence. A arquitetura da Linha de Valor Football Intelligence deve estar preparada para essa integração, sem exigir o desenvolvimento do Value Tracker agora.

No futuro, a empresa poderá atuar em domínios independentes, como Football, Finance, Business e Artificial Intelligence, entre outros. Cada domínio poderá conter diversos produtos.

Essa visão orienta o crescimento, mas não autoriza a criação antecipada de pastas, plataformas, componentes ou projetos. A estrutura física do ecossistema deve surgir conforme necessidades reais, preservando limites que permitam evolução sem reorganizações recorrentes.

## 12. Padrões de decisão e implementação

São regras permanentes:

- nunca criar pastas vazias;
- nunca criar abstrações sem uso real;
- nunca instalar ferramentas antecipadamente;
- nunca escolher frameworks antes da arquitetura;
- sempre preferir soluções simples;
- sempre documentar decisões importantes;
- manter produtos isolados o suficiente para evoluírem de forma independente;
- compartilhar somente aquilo que demonstre valor comum;
- revisar o impacto de toda mudança antes de incorporá-la ao ecossistema.

Reutilização não significa centralização automática. Duplicação pequena e temporária pode ser preferível a uma dependência compartilhada mal compreendida. A extração de componentes comuns deve ocorrer quando os padrões de uso estiverem claros.

## 13. Autoridade e evolução deste documento

Este documento registra fundamentos institucionais. Alterações em missão, visão, papéis, processo oficial, ordem de decisão ou princípios permanentes exigem proposta explícita, análise de impacto e aprovação do Product Owner.

Novas versões devem preservar o histórico por meio do Git. Detalhes operacionais devem permanecer nos documentos especializados, evitando transformar esta Constituição em um manual extenso ou dependente de ferramentas específicas.

Em caso de conflito:

1. uma decisão explícita e mais recente do Product Owner prevalece para o caso em análise;
2. o conflito deve ser registrado e corrigido na documentação aplicável;
3. uma instrução técnica não pode alterar implicitamente um princípio institucional.

## 14. Agenda de evolução institucional

Esta seção reúne recomendações e questões para decisões futuras. Seus itens não constituem políticas aprovadas até que passem pelo processo oficial.

### 14.1 Sugestões de melhoria

- Definir critérios para classificar conhecimento como hipótese, experimento, validado, substituído ou arquivado.
- Estabelecer uma política mínima de propriedade intelectual, confidencialidade e uso de serviços de IA.
- Criar critérios objetivos para iniciar, suspender ou encerrar um produto.
- Definir indicadores de qualidade, aprendizado e valor para acompanhar a evolução da empresa.
- Realizar revisões periódicas do processo para remover burocracia e corrigir lacunas.

### 14.2 Pontos ainda não definidos

- Modelo jurídico e políticas formais da empresa.
- Critérios financeiros para priorização e continuidade de produtos.
- Limites para exposição de dados, estratégias e conhecimento a ferramentas externas de IA.
- Processo de classificação, validação, versionamento e arquivamento do conhecimento.
- Política de segurança, privacidade, backup, recuperação e continuidade.
- Critérios para transformar uma capacidade de produto em componente compartilhado.
- Responsabilidades e níveis de acesso quando novos colaboradores integrarem a equipe.

### 14.3 Riscos futuros

- **Dependência excessiva do fundador:** decisões e conhecimento podem permanecer concentrados e não documentados.
- **Dependência de fornecedores de IA:** mudanças de disponibilidade, preço ou comportamento podem afetar o processo.
- **Confiança indevida em resultados gerados:** respostas plausíveis podem introduzir erros técnicos ou de negócio.
- **Documentação sem manutenção:** fontes divergentes podem comprometer a confiabilidade do contexto institucional.
- **Reutilização prematura:** componentes compartilhados podem aumentar acoplamento e impedir evolução independente.
- **Dispersão de conhecimento:** pesquisas e aprendizados podem se perder entre produtos e ferramentas.
- **Expansão sem critérios:** novos domínios podem dividir atenção antes que a operação esteja preparada.
- **Riscos regulatórios:** produtos relacionados a dados, finanças ou apostas podem exigir controles específicos.

### 14.4 Oportunidades de evolução

- Construir uma base de conhecimento institucional reutilizável por pessoas e agentes de IA.
- Transformar metodologias e modelos validados em vantagens cumulativas entre produtos.
- Automatizar etapas repetitivas depois que o processo manual estiver estável.
- Desenvolver componentes compartilhados a partir de necessidades comprovadas em mais de um produto.
- Criar mecanismos de avaliação para medir a qualidade das contribuições de IA.
- Formar uma arquitetura organizacional capaz de incorporar novos colaboradores sem perder contexto.
- Usar resultados negativos e experimentos descartados como conhecimento para reduzir retrabalho futuro.

## 15. Síntese

A R21 Labs existe para transformar conhecimento em produtos digitais próprios. Sua capacidade de longo prazo depende menos da quantidade imediata de software produzido e mais da qualidade com que objetivos, conhecimento, decisões e entregas são organizados.

O processo protege essa capacidade. Os produtos aplicam o conhecimento. A arquitetura organiza cada solução. A tecnologia serve às decisões anteriores. A inteligência artificial amplia a capacidade da equipe, mas opera dentro de limites explícitos, sob validação e autoridade humana.
