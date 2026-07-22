# Estratégia de testes do Método 1

## 1. Objetivo

Definir como provar correção, determinismo, auditabilidade, segurança e
integração do Método 1 sem usar dados proprietários e sem reabrir os gates do
Pricing Engine `1.0.0`.

Esta estratégia planeja testes futuros; nenhum teste ou código é criado na T01.

## 2. Princípios

- testar regra normativa separadamente de regressão do legado;
- usar somente fixtures sintéticas ou sanitizadas e minimizadas;
- igualdade exata para IDs, códigos, ordem, estados, versões e hashes;
- `NumericPolicy` para comparações `binary64`;
- preservar valores brutos e nunca testar a partir de arredondamento exibido;
- cada decisão `D-M1` possui teste de aceitação rastreável à antiga `M1-PEND`;
- nenhuma suíte pode depender de rede, arquivo privado, Excel ou relógio real.

## 3. Organização futura recomendada

```text
tests/
├── unit/
│   └── models/
│       ├── samples/
│       └── method_one/
├── property/
│   └── models/
├── integration/
│   └── test_method_one_pricing_engine.py
└── fixtures/
    └── synthetic/
```

Essa estrutura não é criada na T01.

## 4. Fixtures sintéticas mínimas

### M1-FX-001 — Base simétrica

Quatro séries com dez observações, pesos iguais, sem ajustes e valores simples.
Valida médias, combinação, explicação e integração nominal.

### M1-FX-002 — Zero observado

Inclui zeros `OBSERVED` em posições recentes e antigas. Valida numerador,
denominador, média e hash sem coerção para ausência.

### M1-FX-003 — Ausência

Mistura observações `MISSING` com valores observados. Confirma exclusão do
denominador, motivo e contagens.

### M1-FX-004 — Não aplicável

Confirma estado e motivo distintos de ausência.

### M1-FX-005 — Inválida e pendente

Valida bloqueio tipado e ausência de resultado parcial enganoso.

### M1-FX-006 — Amostra insuficiente

Cada série possui entre uma e quatro observações. Espera resultado auditável,
qualidade insuficiente e gates negativos, não taxa zero.

### M1-FX-007 — Baixa confiança

Séries com cinco a nove observações e warning explícito.

### M1-FX-008 — Assimetria

Exemplo puramente sintético com dez observações de um lado e sete do outro.
Confirma denominadores independentes, warning e qualidade agregada pela pior
série, conforme `D-M1-006`.

### M1-FX-009 — Datas empatadas

Partidas com o mesmo instante e IDs diferentes. Confirma desempate, ordem e hash
determinísticos.

### M1-FX-010 — Sobreposição legítima

Uma partida aparece em séries contextuais distintas, mas nunca duplicada dentro
da mesma identidade. Confirma registro de sobreposição.

### M1-FX-011 — Ajustes

Multiplicadores identidade, dentro da faixa e exceção aprovada. Inclui
candidatos de partida, campeonato e global na mesma categoria, confirma o único
valor efetivo e audita escolhidos e descartados conforme `D-M1-004`.

### M1-FX-012 — Elegibilidade de distribuição

Taxa de gols aprovada converte para `PoissonRate`; estatística futura não
aprovada retorna `MODEL_NOT_APPLICABLE`.

### M1-FX-013 — Sensibilidade de hash

Alterar uma observação, ordem semântica, filtro, peso, ajuste ou versão altera o
hash correspondente.

### M1-FX-014 — Repetibilidade

Executar a mesma entrada várias vezes no mesmo processo e em processos
separados produz objetos, bytes e hashes idênticos.

## 5. Testes unitários de observações

- criar valor observado positivo e zero;
- rejeitar `NaN`, infinitos, booleanos e tipo incorreto;
- rejeitar contagem negativa no escopo inicial;
- impedir valor utilizável em estado não observado;
- distinguir todos os estados de qualidade;
- validar unidade, estatística e período;
- validar participante, adversário, papel e condição;
- exigir timezone no instante da partida;
- garantir identidade estável da observação.

## 6. Testes unitários de amostra

- suportar 5, 10, 15, 20, temporada e período personalizado;
- suportar casa, fora e geral sem confundir o preset inicial;
- aplicar corte temporal e rejeitar observação futura;
- ordenar por instante decrescente e ID crescente;
- detectar duplicidade dentro da série;
- preservar IDs considerados, usados e excluídos;
- reconciliar todas as contagens e exclusões;
- validar versão/hash dos dados e filtros;
- excluir canceladas, anuladas, interrompidas, W.O. e disputas por pênaltis;
- excluir prorrogação e aceitar somente tempo regulamentar claramente separado
  e validado;
- marcar estado incerto como `PENDING_REVIEW`, excluir da média e bloquear uso
  automático;
- rejeitar mais de 1.000 observações por snapshot.

## 7. Testes unitários de médias

- média uniforme manual conhecida;
- zero participa do numerador e denominador;
- ausente e não aplicável não participam;
- inválido, suspeito e pendente seguem política;
- média vazia retorna `SAMPLE_EMPTY`;
- `1–4`, `5–9` e `10+` produzem qualidades corretas;
- somente `OBSERVED` entra no denominador e zero observado permanece válido;
- `math.fsum` é usado para soma relevante;
- `uniform/v1` atribui pesos iguais e usa ordem `occurred_at DESC, match_id ASC`;
- recência não uniforme não é executável na implementação inicial;
- pesos desalinhados, negativos, não finitos ou com soma inválida falham;
- ordem de observações uniformes não altera valor, mas a ordem canônica do
  snapshot permanece estável.

## 8. Testes da combinação

- exemplos manuais de mandante e visitante;
- exemplo canônico confirma `0.50 * 1.60 + 0.50 * 1.10 = 1.35` e
  `1.35 * 1.05 * 0.95 = 1.346625`;
- peso próprio `1` e adversário `0`;
- peso próprio `0` e adversário `1`;
- pesos fora de `[0,1]`;
- soma diferente de `1` dentro e fora da tolerância;
- nenhuma normalização silenciosa;
- ausência de ponderação implícita por número de jogos;
- explicação reconcilia termos e taxa base;
- fórmula e pesos mudam o hash.

## 9. Testes dos ajustes

- nenhum ajuste preserva a taxa base;
- multiplicador `1.0` é identidade;
- sequência conhecida reconcilia cada etapa;
- multiplicador zero, negativo ou não finito falha;
- exceção fora de `0,90–1,10` exige metadados aprovados;
- código desconhecido, duplicado ou não aplicável falha;
- precedência `partida → campeonato → global` escolhe um valor por categoria;
- candidatos efetivos e descartados preservam valor, fonte e motivo;
- política explícita produz warning ou erro para exceções, sem clamp;
- ordem canônica é preservada;
- taxa negativa ou não finita nunca é produzida;
- alteração isolada de ajuste altera resultado e hash.

## 10. Testes de qualidade, warnings e erros

- componente vazio bloqueia cálculo;
- amostra `1–4` retorna resultado auditável com warning grave e bloqueia
  aprovação e publicação;
- amostra `5–9` retorna baixa confiança, warning e publicação condicionada a
  permissão e justificativa;
- amostra `10+` retorna confiança padrão;
- qualidade agregada corresponde à pior série;
- quantidade encontrada menor que solicitada gera warning;
- assimetria gera warning e preserva os quatro denominadores independentes;
- temporada anterior, recorte personalizado, suspeitas e sobreposição são
  registrados;
- warning não altera taxa matemática;
- mensagens e contextos não contêm nomes, caminhos ou valores privados;
- erro não é convertido em vazio, zero ou resultado parcial.

## 11. Property-based tests

- média uniforme permanece entre mínimo e máximo observados;
- adicionar uma cópia de cada observação preserva a média;
- escala por constante não negativa escala médias e taxas na mesma proporção
  quando ajustes são identidade;
- peso `1/0` seleciona exatamente o primeiro componente;
- trocar mandante e visitante e suas quatro séries troca as taxas, sob
  configuração simétrica;
- permutar input equivalente antes da canonicalização preserva resultado e
  hash canônico;
- duplicar uma identidade sempre falha;
- zero observado nunca reduz o denominador;
- estados não observados nunca aumentam o denominador;
- pesos válidos formam combinação dentro do intervalo das duas médias;
- produto de multiplicadores positivos preserva não negatividade;
- objetos públicos não expõem mutação observável;
- serialização seguida de repetição produz bytes idênticos.

## 12. Regressão

### 12.1 Regressão normativa

Fixtures sintéticas congelam resultados da fórmula aprovada, schemas, hashes e
warnings. Possuem precedência sobre comportamento acidental do XLSM.

### 12.2 Regressão histórica

Casos sanitizados mínimos podem reproduzir:

- média aritmética com vazios;
- pesos observados `0,5/0,5`;
- exemplo documental `0,6/0,4`;
- produto de multiplicadores observado.

Cada caso será rotulado como evidência histórica. Divergência deliberada por
regra aprovada será explicada e versionada.

### 12.3 Dados privados

A suíte privada permanece fora do Git. Nenhuma fixture pública poderá conter
nomes de times, partidas, datas, fontes, caminhos, IDs ou séries históricas
reidentificáveis.

## 13. Integração com o Pricing Engine 1.0.0

- converter somente taxa elegível e finita em `PoissonRate`;
- aceitar somente `goals/first_half` e `goals/regulation_time`;
- rejeitar escanteios, finalizações, chutes no gol, cartões e faltas com
  `MODEL_NOT_APPLICABLE` nesta Initiative;
- construir `PricingRequest` sem ampliar schema v1;
- executar `run_pricing_engine` com mercados sintéticos aprovados;
- verificar que taxas do Método 1 chegam sem arredondamento;
- tratar `CalculationError` do Método 1 antes de chamar o engine;
- impedir integração de qualidade vazia ou estatística não elegível;
- executar primeiro tempo e partida em requests separados;
- correlacionar hash do Método 1 e hash do `PricingResult` no envelope;
- garantir que hashes de regressão existentes do engine permanecem idênticos;
- confirmar que o Método 1 não seleciona mercados nem chama o engine.

## 14. Serialização e hash

- chaves em ordem canônica e tuplas em ordem semântica;
- floats por `float.hex()` e `-0.0` conforme política canônica aprovada;
- ausência explícita e estados codificados;
- IDs, filtros, versões, amostras, pesos, ajustes e resultados no hash;
- metadados voláteis excluídos;
- hash SHA-256 em minúsculas;
- mudança em conteúdo determinístico altera hash;
- mudança em duração, host ou correlação operacional não altera hash;
- schema incompatível falha de forma tipada;
- serialização não recalcula nem arredonda.

## 15. Determinismo e imutabilidade

- repetição no mesmo processo;
- repetição em processo novo;
- ordem alternativa equivalente de input;
- ausência de relógio, UUID, random e `hash()` nativo;
- frozen dataclasses, tuplas e `mappingproxy`;
- tentativas de mutação falham;
- igualdade depende de conteúdo;
- nenhuma cache mutável participa do resultado.

## 16. Ausência de I/O e segurança

Varredura estática do runtime futuro deverá rejeitar:

- `open`, `pathlib` para I/O, sockets e clientes de rede;
- banco, subprocesso e shell;
- `os.environ` e leitura de ambiente;
- Excel, execução dinâmica, `eval` e `exec`;
- logging de saída no núcleo;
- dependências externas de runtime.

Testes dinâmicos deverão executar o Método 1 com acessos a arquivo, rede,
subprocesso e ambiente bloqueados, comprovando que nenhuma dessas capacidades é
necessária.

## 17. Desempenho

Benchmark somente com dados sintéticos, em CPython 3.13 e ambiente registrado:

- quatro snapshots de 20 observações, 1.000 iterações após aquecimento: p95 de
  até 10 ms;
- quatro snapshots de 1.000 observações: p95 de até 100 ms;
- memória adicional no payload máximo: até 10 MiB;
- medir separadamente validação, cálculo e serialização;
- comprovar uma passagem por snapshot e ausência de recomputações óbvias.

Falha do orçamento exige perfil e decisão; não autoriza NumPy, pandas ou outra
dependência automaticamente.

## 18. Gates de qualidade

Na validação final futura:

- pytest completo aprovado;
- 100% de linhas e branches, mantendo o gate vigente do pacote;
- mypy strict aprovado;
- Ruff check e format check aprovados;
- `compileall` e `pip check` aprovados;
- build e instalação limpa aprovados;
- hashes e integração determinísticos;
- nenhuma regressão no engine `1.0.0`;
- nenhuma fixture privada ou dependência de runtime;
- documentação da API e limites atualizada.

## 19. Critérios de aceite da estratégia

- todos os estados de observação possuem casos positivos e negativos;
- todas as decisões `M1-PEND-001–007 → D-M1-001–007` possuem testes
  rastreáveis;
- fórmula, pesos, recência, ajustes, assimetria e estados especiais possuem
  evidência específica;
- testes distinguem cálculo auditável de elegibilidade para aprovação;
- integração prova separação entre taxa, distribuição e mercado;
- segurança e desempenho usam apenas dados sintéticos.

## 20. Referências

- [Plano técnico](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Decisões matemáticas](17-method-one-mathematical-decisions.md)
- [Backlog](19-method-one-implementation-backlog.md)
- [Gate](20-method-one-planning-gate.md)
