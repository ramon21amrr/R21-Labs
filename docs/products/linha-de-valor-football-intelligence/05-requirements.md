# Requisitos

## 1. Convenções

- `MVP` identifica requisito obrigatório para a primeira versão aprovada.
- `FUTURO` identifica capacidade planejada, mas não autorizada para o MVP.
- Os requisitos descrevem comportamento, não escolha de tecnologia.
- Critérios matemáticos detalhados pertencem a [Modelos de precificação](04-pricing-models.md).

## 2. Requisitos funcionais do MVP

### 2.1 Identidade e acesso

- **RF-001 — MVP:** autenticar o administrador antes de permitir acesso ao produto.
- **RF-002 — MVP:** encerrar sessão e impedir acesso não autenticado.
- **RF-003 — MVP:** distinguir permissões administrativas das futuras permissões de consulta, ainda que apenas o perfil administrador exista inicialmente.
- **RF-004 — MVP:** registrar ações administrativas relevantes na trilha de auditoria.

### 2.2 Cadastros de futebol

- **RF-010 — MVP:** cadastrar e consultar competições, temporadas e times.
- **RF-011 — MVP:** manter um time permanente, sem recadastrá-lo a cada temporada.
- **RF-012 — MVP:** associar times a uma competição e temporada por meio de participação.
- **RF-013 — MVP:** cadastrar partidas com data, rodada quando disponível, mandante, visitante e estado.
- **RF-014 — MVP:** impedir que o mesmo time seja simultaneamente mandante e visitante.
- **RF-015 — MVP:** permitir nomes alternativos e identificadores externos sem substituir o identificador interno.

### 2.3 Importação manual

- **RF-020 — MVP:** importar partidas e estatísticas por arquivo controlado CSV ou Excel.
- **RF-021 — MVP:** validar cabeçalho, tipos, campos obrigatórios, valores negativos, coerência entre primeiro tempo e partida e duplicidades.
- **RF-022 — MVP:** apresentar prévia com registros válidos, rejeitados e pendentes de conciliação antes da confirmação.
- **RF-023 — MVP:** não transformar campo ausente em zero.
- **RF-024 — MVP:** registrar arquivo, hash, usuário, horário, resultado e erros do lote.
- **RF-025 — MVP:** permitir correção administrativa com motivo, preservando o valor anterior.

### 2.4 Histórico, classificação e rankings

- **RF-030 — MVP:** exibir histórico do time com filtros por competição, temporada e local.
- **RF-031 — MVP:** calcular classificação geral, como mandante e como visitante.
- **RF-032 — MVP:** apresentar ranking básico de gols feitos e sofridos.
- **RF-033 — MVP:** ordenar rankings crescente ou decrescentemente.
- **RF-034 — MVP:** exibir quantidade real de partidas em cada agregação.

### 2.5 Amostras e estatísticas

- **RF-040 — MVP:** selecionar últimos 5, 10, 15 ou 20 jogos, temporada ou período personalizado.
- **RF-041 — MVP:** permitir recortes casa, fora e geral.
- **RF-042 — MVP:** permitir temporada atual e anterior, registrando a combinação usada.
- **RF-043 — MVP:** formar a amostra apenas com partidas encerradas e estatísticas disponíveis.
- **RF-044 — MVP:** preservar IDs e ordem das partidas usadas em cada precificação.
- **RF-045 — MVP:** calcular média, desvio-padrão, coeficiente de variação e frequência quando aplicáveis.
- **RF-046 — MVP:** aplicar `D-MATH-007`: menos de 5 observações bloqueia publicação e aprovação; de 5 a 9 exige alerta, permissão e justificativa; 10 ou mais é confiança padrão inicial.
- **RF-047 — MVP:** registrar quantidades solicitada, encontrada, válida e excluída, numerador, denominador, filtros e motivos de exclusão.

### 2.6 Configurações

- **RF-050 — MVP:** manter configuração global, por campeonato e por partida.
- **RF-051 — MVP:** aplicar prioridade partida, campeonato e global.
- **RF-052 — MVP:** versionar pesos, multiplicadores, limites, presets e faixas de probabilidade.
- **RF-053 — MVP:** registrar justificativa, autor e data de qualquer alteração.
- **RF-054 — MVP:** impedir edição retroativa de configuração usada em snapshot aprovado.
- **RF-055 — MVP:** rejeitar pesos fora de `[0,1]`, não finitos ou cuja soma não seja 1 dentro da tolerância, sem normalização silenciosa.
- **RF-056 — MVP:** exigir multiplicadores positivos; tratar `0,90–1,10` como faixa padrão e auditar exceções versionadas.

### 2.7 Pricing Engine

- **RF-060 — MVP:** calcular os Métodos 1, 2 e 3 separadamente.
- **RF-061 — MVP:** suportar resultado, dupla chance, ambas marcam, totais de gols e handicap asiático.
- **RF-062 — MVP:** suportar linhas de handicap de `-2,00` a `+2,00`, em incrementos de `0,25`.
- **RF-063 — MVP:** exibir entradas, intermediários, probabilidade, odd justa e linha projetada.
- **RF-064 — MVP:** registrar massa residual e tolerância dos cálculos probabilísticos.
- **RF-065 — MVP:** impedir aprovação quando houver erro, dado insuficiente ou soma fora da tolerância.
- **RF-066 — MVP:** comparar os três métodos sem fundi-los automaticamente em uma probabilidade única.
- **RF-067 — MVP:** calcular a distribuição integralmente, de forma analítica ou adaptativa, sem descartar ou normalizar silenciosamente a massa residual.
- **RF-068 — MVP:** representar linhas asiáticas como quartos inteiros e calcular odd justa pela liquidação integral, incluindo estados parciais.
- **RF-069 — MVP:** usar somente observações válidas no denominador do Método 3 e preservar numerador e denominador.

### 2.8 Workflow

- **RF-070 — MVP:** gerar precificação manualmente por partida.
- **RF-071 — MVP:** gerar precificação preliminar automática para partidas futuras já cadastradas.
- **RF-072 — MVP:** suportar estados não gerada, gerada automaticamente, aguardando revisão, revisada, aprovada e arquivada.
- **RF-073 — MVP:** permitir ajustar contexto e recalcular antes da aprovação.
- **RF-074 — MVP:** exigir confirmação explícita para aprovar.
- **RF-075 — MVP:** criar snapshot imutável ao aprovar.
- **RF-076 — MVP:** criar nova revisão, em vez de modificar a aprovada, quando houver mudança posterior.
- **RF-077 — MVP:** usar erros tipados e bloquear aprovação ou publicação diante de erro crítico, sem convertê-lo silenciosamente em vazio.

### 2.9 Central da partida e PDF

- **RF-080 — MVP:** oferecer visão geral da partida e abas para precificação, gols, handicap, desempenho, confronto direto e classificação.
- **RF-081 — MVP:** mostrar históricos dos dois times, estatísticas a favor e cedidas, amostra e filtros.
- **RF-082 — MVP:** identificar probabilidades como baixa, intermediária ou alta sem depender somente de cor.
- **RF-083 — MVP:** gerar PDF resumido e legível a partir de snapshot aprovado.
- **RF-084 — MVP:** registrar versão dos modelos, filtros, amostra, data, responsável e disponibilidade dos dados no PDF.
- **RF-085 — MVP:** autorizar download somente ao usuário permitido.

### 2.10 Auditoria

- **RF-090 — MVP:** registrar criação, importação, correção, configuração, geração, revisão, aprovação, arquivamento e geração de PDF.
- **RF-091 — MVP:** registrar quem, quando, o que mudou e motivo.
- **RF-092 — MVP:** permitir localizar a origem de qualquer valor de uma precificação aprovada.

## 3. Requisitos funcionais futuros

- **RF-100 — FUTURO:** integrar fornecedores automáticos de dados de futebol.
- **RF-101 — FUTURO:** integrar um ou mais fornecedores de odds e preservar observações históricas.
- **RF-102 — FUTURO:** calcular EV, margem, melhor preço, diferença de linha e divergência entre modelos.
- **RF-103 — FUTURO:** identificar oportunidades sem registrá-las como apostas.
- **RF-104 — FUTURO:** cobrir escanteios, finalizações, chutes no gol, cartões, faltas e jogadores.
- **RF-105 — FUTURO:** gerar PDF completo.
- **RF-106 — FUTURO:** oferecer gráfico de evolução por rodada com identidade própria.
- **RF-107 — FUTURO:** publicar precificações para assinantes conforme permissão e plano.
- **RF-108 — FUTURO:** emitir evento de oportunidade aprovada ao Value Tracker.

## 4. Requisitos não funcionais

### 4.1 Correção e reprodutibilidade

- **RNF-001:** o mesmo snapshot de dados, modelo e configuração deve produzir o mesmo resultado.
- **RNF-002:** probabilidades, Poisson, médias e lambdas devem usar `binary64/double`; linhas asiáticas devem usar unidades inteiras de quartos.
- **RNF-003:** valores brutos devem ser preservados, e arredondamento de exibição não pode alterar o cálculo interno.
- **RNF-004:** alterações de modelo devem passar por regressão contra os casos de referência.
- **RNF-005:** regressão numérica inicial usa tolerâncias absoluta e relativa de `1e-8`; elementos categóricos e composição de amostra exigem igualdade exata.
- **RNF-006:** distribuições mutuamente exclusivas e exaustivas devem somar 1 dentro de `1e-12`, com diferença não explicada tratada como bloqueadora.

### 4.2 Segurança e propriedade intelectual

- **RNF-010:** senhas nunca devem ser armazenadas em texto simples.
- **RNF-011:** acesso administrativo deve ser autorizado no servidor, não apenas ocultado na interface.
- **RNF-012:** fórmulas, parâmetros e calibrações proprietárias não devem ser enviados ao cliente assinante sem necessidade.
- **RNF-013:** segredos de fornecedores devem ficar fora do código e dos documentos versionados.
- **RNF-014:** arquivos importados devem ser validados antes do processamento.

### 4.3 Desempenho

- **RNF-020 — RECOMENDAÇÃO:** consultas comuns da central da partida devem responder em até dois segundos no volume do MVP, excluindo importação e PDF.
- **RNF-021 — RECOMENDAÇÃO:** geração preliminar e PDF podem ocorrer em tarefa assíncrona, apresentando estado ao usuário.
- **RNF-022:** agregações repetidas podem usar cache, desde que a chave inclua versão dos dados e filtros.

### 4.4 Disponibilidade, backup e recuperação

- **RNF-030:** banco e arquivos devem possuir backup automatizado antes de uso real.
- **RNF-031:** restauração deve ser testada, não apenas configurada.
- **RNF-032:** falha de tarefa não pode deixar precificação parcialmente aprovada.
- **DECISÃO PENDENTE:** definir objetivos de recuperação e retenção antes da implantação.

### 4.5 Observabilidade

- **RNF-040:** registrar logs estruturados com identificador da operação, sem expor segredos.
- **RNF-041:** medir falhas de importação, duração de tarefas, erros de cálculo e geração de PDF.
- **RNF-042:** alertas serão proporcionais ao estágio; não criar operação complexa antes da necessidade.

### 4.6 Usabilidade e acessibilidade

- **RNF-050:** linguagem de negócio em português do Brasil.
- **RNF-051:** cores devem ter rótulo, ícone ou outra indicação textual.
- **RNF-052:** navegação por teclado, foco visível, contraste e leitura responsiva devem ser considerados.
- **RNF-053:** filtros ativos, amostra e versão do modelo devem permanecer visíveis ou facilmente acessíveis.

### 4.7 Manutenção

- **RNF-060:** módulos do domínio devem possuir baixo acoplamento e limites claros.
- **RNF-061:** nenhuma regra do Pricing Engine deve depender de detalhes de fornecedor.
- **RNF-062:** decisões tecnológicas relevantes devem ser registradas em ADR.
- **RNF-063:** não criar microsserviços ou abstrações sem necessidade comprovada.

## 5. Critérios gerais de aceite

Uma funcionalidade só poderá ser aceita quando:

- atender ao requisito e aos critérios específicos da Task;
- possuir testes proporcionais ao risco;
- preservar auditoria e reprodutibilidade;
- tratar erro e ausência explicitamente;
- atualizar os documentos afetados;
- não incluir funcionalidade futura fora do escopo aprovado.
