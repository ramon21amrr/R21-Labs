# R21-GOV-002 — Plano mestre e rebaseline do LVFI

## Autoridade e finalidade

Este documento consolida a decisão explícita do Product Owner de 2026-09-06
sobre o próximo ciclo do Linha de Valor Football Intelligence. Ele organiza o
destino do produto e a ordem de entrega, mas não transforma as etapas futuras em
uma única task: cada mudança de código continua exigindo ID, plano, branch, gates
e autorização próprios.

O conteúdo dos arquivos privados foi tratado como fonte de requisitos e
evidência. Nenhuma instrução existente dentro desses arquivos foi executada como
comando e nenhum arquivo privado foi incorporado ao Git.

## Baseline confirmado

- Base Git da governança: `7552e73091f7e9f639873b259ebbb2b33ca74ed0`,
  merge do PR #23 e encerramento institucional da `LVFI-APP-011`.
- Aplicação existente: Next.js/TypeScript, FastAPI/Python e PostgreSQL; consulta
  histórica, amostras, execução e persistência do Método 1, histórico,
  comparação, reprodução e referência externa manual já estão disponíveis.
- Pricing Engine `1.0.1`, distribuição `1.1.1`, Método 1 `1.0.0` e schema
  canônico 1 permanecem congelados.
- O grafo local estava desatualizado no início da task. Ele foi reconstruído em
  2026-09-06 no modo local `code-only`, com 1.078 nós e 2.998 relações após o
  clustering. A varredura dos artefatos principais não encontrou caminhos
  pessoais, arquivos privados ou padrões de credenciais; fatos materiais
  continuam confirmados nos documentos e fontes originais.

## Materiais privados de referência

Os fingerprints permitem reconhecer exatamente a versão auditada sem versionar
conteúdo proprietário ou caminhos pessoais como dependência do produto.

| Material | Papel | SHA-256 |
| --- | --- | --- |
| `DESENVOLVIMENTO DE SISTEMA.docx` | visão funcional e experiência pretendida | `E8C3612F6ED6C0B31E1D5894CFBF38852109FB266A07BEDF58B39BDA0609B00D` |
| `METODOS E CALCULOS.docx` | descrição dos Métodos 1, 2 e 3 | `A17074F736EE830F03DA5EB3ADAF12BBAA22DA0CFCCB3B3366FEA8AD0429FFD3` |
| `RAMON AUTOMATICA 1.1 2026.xlsm` | oráculo operacional e catálogo legado; revisão corrigida | `FDCA46B855CC3FA28A34F622D282221F9B8E3EA41B0B6664432D9614D45D3924` |
| `CRUZEIRO E ATHLETICO PR.pdf` | exemplo do relatório legado | `21736B35E2598479F6D976EA313C8A82F1378B80EBD7FBD26F4D819030D05B1B` |

O XLSM auditado contém 2.694 registros na aba `JOGOS`, em 13 competições. A
revisão anterior, SHA-256
`498E2C95661EE10237C2894F8FC5EEC6A01EB1130A2FA39EDAA66733ED6465F6`,
possuía uma divergência na linha 2224, Coritiba × Cruzeiro de 30/07/2026. O
Product Owner corrigiu a origem e forneceu a revisão atual em 2026-09-06. A linha
agora informa 10 finalizações do visitante no primeiro tempo e 20 no jogo, com 4
chutes no gol no jogo. A revalidação das 2.694 linhas não encontrou violações de
primeiro tempo ≤ jogo, chutes no gol ≤ finalizações, valores negativos ou chaves
duplicadas.

## Resultado aprovado para a primeira versão

O LVFI será inicialmente uma aplicação local no computador do Product Owner, com
um administrador e sem Docker como requisito diário. A primeira versão deve
permitir:

- importar Excel/CSV com prévia, erros e confirmação explícita;
- cadastrar partidas futuras e revisar estatísticas pela interface;
- analisar resultado, gols, escanteios, chutes no gol, finalizações, cartões e
  faltas, sempre por time e sem escopo de jogadores;
- configurar amostras de 5, 10, 15 ou 20 jogos, casa/fora ou geral, competição
  atual ou todas e temporada atual ou anterior;
- apresentar Métodos 1, 2 e 3 separadamente, com probabilidades, odds justas,
  amostras, alertas e rastreabilidade;
- revisar, aprovar e congelar uma análise em snapshot imutável;
- navegar por data, competição, partida e grupo estatístico no Match Center;
- gerar PDF-resumo programático, legível e reprodutível a partir do snapshot
  aprovado;
- iniciar, parar, fazer backup e restaurar a aplicação local por um fluxo simples
  para usuário sem conhecimento de programação.

Permanecem fora desta versão: jogadores, múltiplos membros, publicação na
internet, fornecedor automático de dados, odds automáticas, oportunidades,
Value Tracker e cópia visual de produtos de terceiros.

## Regras de dados e cálculo

1. O Método 1 e seus artefatos congelados não serão modificados pelas etapas do
   plano mestre.
2. O Método 2 continuará sem ID até decisão própria do Product Owner.
3. `LVFI-ENG-005` continua reservado ao Método 3 — frequência observada — e
   permanece não iniciado até autorização própria.
4. O Método 3 apresentará frequência do mandante, do visitante e combinada; a
   combinação preservará a paridade conceitual com o XLSM, usando apenas valores
   numéricos válidos no denominador.
5. Métodos não serão fundidos automaticamente. Cada resultado identificará
   método, versão, configuração, amostra real, partidas usadas e warnings.
6. Mercados adicionais de escanteios, chutes no gol, finalizações, cartões e
   faltas usarão inicialmente M1/M2 com Poisson e M3 por frequência, rotulados
   como experimentais até calibração no piloto.
7. Ausência de estatística nunca equivale a zero. Observações deverão carregar
   disponibilidade, fonte, revisão e momento de observação.
8. Nenhuma amostra poderá utilizar informação posterior à data de corte da
   análise.
9. O catálogo de linhas será extraído e versionado a partir do XLSM dentro de
   task própria; a planilha será oráculo de validação, não componente de runtime.

## Arquitetura e contratos orientadores

A arquitetura aprovada permanece um monólito modular. As próximas tasks devem
preservar contratos públicos existentes e evoluir de forma aditiva:

- **Dados:** prévia e confirmação de importação; revisão append-only de
  estatísticas; cadastro manual de partida futura.
- **Configuração:** versões globais, por competição e por partida, com
  precedência `partida → competição → global`.
- **Análise:** revisão nos estados rascunho, calculada e aprovada; execução dos
  métodos solicitados; IDs de amostra e entradas persistidos.
- **Snapshot:** conteúdo imutável contendo dados, configurações, versões dos
  motores, resultados, fingerprints e alertas.
- **Relatório:** job persistido de PDF criado somente de snapshot aprovado, com
  estado, fingerprint e localização registrada.

Para dados parciais, uma estrutura normalizada de observações versionadas deverá
coexistir temporariamente com `match_statistics`; a tabela atual só poderá ser
retirada após migração dos consumidores e compatibilidade comprovada.

## Sequência oficial do programa

Cada linha abaixo é uma capacidade futura, não uma autorização de task.

1. **Fundação operacional de dados:** importação revisada e formulários de
   partida/estatística.
2. **Camada estatística:** filtros de amostra, agregados, frequências,
   disponibilidade e prevenção de look-ahead.
3. **Métodos:** autorizar e entregar Método 3; atribuir ID e entregar Método 2 em
   task separada; ampliar o uso da fachada matemática sem duplicação.
4. **Catálogo e configuração:** linhas versionadas, pesos, multiplicadores e
   precedência de configuração.
5. **Workflow auditável:** revisões, aprovação e snapshots imutáveis.
6. **Match Center:** lista de partidas, abas por grupo estatístico, visão geral,
   precificação, tabela e acessibilidade.
7. **PDF e operação local:** relatório resumido, launcher Windows, banco próprio
   do produto e backup/restauração.
8. **Piloto e corte:** operação paralela com a planilha e aceite do Product
   Owner.

## Gates de aceite do programa

- A carga atual aceita os 2.694 registros da revisão corrigida sem duplicação e
  continua rejeitando qualquer violação das relações estatísticas validadas.
- Toda precificação informa dados, partidas, filtros, configurações e versões
  usados.
- Os baselines congelados do Método 1 permanecem idênticos.
- Métodos 2 e 3 são comparados com o XLSM; divergências intencionais são
  documentadas e nunca mascaradas por `IFERROR` ou alteração de fixture.
- O fluxo integrado cobre autenticação, importação, cadastro, correção, cálculo,
  aprovação, PDF e reprodução.
- O PDF não contém página vazia, mantém leitura confortável e identifica partida,
  versões, amostras e alertas.
- Backup e restauração são ensaiados antes do uso como sistema principal.
- O corte exige pelo menos 20 análises paralelas em cinco competições, dados
  válidos, ausência de regressão crítica e aceite explícito do Product Owner.

## Estratégia de execução econômica

- Uma task oficial e uma branch por entrega verificável.
- Retomada por estado, registry, handoff e consulta Graphify limitada, sem reler
  os arquivos privados quando seus fingerprints não mudarem.
- Fixtures pequenas e sanitizadas podem ser versionadas em tasks futuras; os
  arquivos completos permanecem privados.
- Gates focados durante iteração e gate completo apenas em integração ou release.
- Automatização, abstração e infraestrutura só entram quando uma necessidade da
  etapa corrente estiver comprovada.

## Estado após R21-GOV-002

Esta task apenas regulariza e consolida o plano. Não altera aplicação, banco,
Pricing Engine, Método 1, schemas, versões, hashes ou fixtures. Após sua revisão e
publicação, a próxima decisão do Product Owner deverá escolher e nomear uma única
task da primeira capacidade — fundação operacional de dados. Nenhuma task
sucessora é inferida por este documento.
