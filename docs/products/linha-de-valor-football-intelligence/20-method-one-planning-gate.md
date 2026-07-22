# Gate de planejamento do Método 1

## 1. Identificação

- **Initiative:** `LVFI-ENG-003`
- **Task avaliada:** `LVFI-ENG-003-T01`
- **Componente futuro:** Método 1 — médias com contexto
- **Dependência aceita:** Pricing Engine `1.0.0`
- **Data do diagnóstico:** 2026-07-21

## 2. Resultado histórico da T01

**BASELINE HISTÓRICA — NO-GO PARA IMPLEMENTAÇÃO MATEMÁTICA DO MÉTODO 1.**

No encerramento original da T01, o planejamento técnico, o catálogo de
contratos, a estratégia de testes e o backlog estavam definidos, mas sete
decisões de produto e matemática ainda não possuíam aprovação explícita. A
implementação não podia escolher essas regras por inferência, conveniência
técnica ou comportamento do legado.

Esse gate histórico não autorizava `LVFI-ENG-003-T02` nem qualquer alteração de
código. A reavaliação posterior está registrada na seção 12.

## 3. Estado inicial verificado

- repositório institucional correto;
- branch `main`;
- working tree limpa antes da documentação;
- `HEAD` e `origin/main` em
  `7da4b0bc8c980597ae970ef4165b94a649af4b94`;
- Pricing Engine `1.0.0` presente;
- validação final da ENG-002 presente;
- `requirements-dev.lock` íntegro;
- nenhum artefato temporário;
- nenhum trabalho anterior da ENG-003.

## 4. Entregas da T01

- [Plano técnico](15-method-one-technical-plan.md);
- [Catálogo de contratos](16-method-one-contract-catalog.md);
- [Decisões matemáticas](17-method-one-mathematical-decisions.md);
- [Estratégia de testes](18-method-one-test-strategy.md);
- [Backlog](19-method-one-implementation-backlog.md);
- este gate.

## 5. Decisões aprovadas preservadas

- fronteira pura e sem I/O;
- Pricing Engine recebe taxas já normalizadas;
- `binary64/float`, tolerâncias e ausência de arredondamento interno;
- zero observado distinto de ausência;
- erros tipados;
- categorias de tamanho e confiança da amostra;
- pesos finitos em `[0,1]` e soma `1`;
- multiplicadores positivos e política de exceção;
- versionamento, hashes e imutabilidade;
- contratos comuns podem ser reutilizados sem incorporar regras dos Métodos 2 e
  3.

## 6. Pendências bloqueadoras na baseline histórica

Todas as pendências desta seção foram posteriormente encerradas por
`D-M1-001–007`, conforme a seção 12.

### 6.1 `M1-PEND-001` — fórmula canônica de combinação — encerrada

Naquele momento, não havia aprovação explícita da média aritmética ponderada
como fórmula normativa.

**Necessário para liberar:** fórmula, versão e aplicabilidade aprovadas.

### 6.2 `M1-PEND-002` — pesos globais iniciais — encerrada

O legado usava `0,5/0,5`, enquanto o exemplo documental usava `0,6/0,4`.

**Necessário para liberar:** valores ou política de configuração obrigatória.

### 6.3 `M1-PEND-003` — ausência de recência no MVP — encerrada

Naquele momento, não existia fórmula de recência aprovada.

**Necessário para liberar:** aprovação da política uniforme ou especificação
completa de alternativa.

### 6.4 `M1-PEND-004` — composição dos multiplicadores — encerrada

O produto simples era observado e recomendado, mas permanecia pendente.

**Necessário para liberar:** fórmula, ordem e catálogo aplicável por estatística.

### 6.5 `M1-PEND-005` — escopo inicial de estatísticas e elegibilidade para Poisson — encerrada

Não estava aprovado quais estatísticas e períodos integrariam a primeira versão
nem quais poderiam virar `PoissonRate`.

**Necessário para liberar:** catálogo inicial e política de elegibilidade de
distribuição.

### 6.6 `M1-PEND-006` — aceitação de amostras assimétricas — encerrada

O comportamento do Método 1 para tamanhos diferentes não estava aprovado.

**Necessário para liberar:** aceitar, equalizar ou bloquear, incluindo warnings.

### 6.7 `M1-PEND-007` — política dos estados especiais de partida — encerrada

Anuladas, interrompidas, W.O., prorrogação e pênaltis não possuíam política
aprovada.

**Necessário para liberar:** elegibilidade por estado, período e estatística.

## 7. Recomendações da baseline, posteriormente aprovadas

- média aritmética ponderada de produção e concessão;
- preset global neutro `0,5/0,5`;
- recência uniforme no MVP;
- produto ordenado dos multiplicadores;
- gols de primeiro tempo e tempo regulamentar como escopo inicial;
- Poisson somente para combinações explicitamente autorizadas;
- amostras assimétricas aceitas com denominadores separados e warning;
- política conservadora para estados especiais de partida.

Na baseline histórica, essas recomendações não possuíam efeito normativo. Elas
foram posteriormente formalizadas por `D-M1-001–007`.

## 8. Condições históricas para novo gate

O novo gate poderia ser solicitado quando:

1. o Product Owner decidir explicitamente os sete itens;
2. o documento 17 for atualizado com o estado aprovado e referência do aceite;
3. fórmula, configuração, schemas e testes forem reconciliados com as decisões;
4. o backlog for revisado se alguma escolha alterar contratos ou sequência;
5. a próxima Task possuir plano próprio aprovado.

Somente então poderia ser avaliado `GO`, `GO COM CONDIÇÕES` ou manutenção do
`NO-GO`.

## 9. Proibições durante o NO-GO histórico

- não criar contratos Python;
- não criar diretórios de implementação;
- não alterar o Pricing Engine `1.0.0`;
- não iniciar T02;
- não implementar médias, pesos ou ajustes;
- não criar integração, serialização ou fixtures;
- não escolher distribuição por inferência;
- não instalar dependências;
- não usar dados proprietários no Git.

## 10. Verificações documentais requeridas

Antes do encerramento da T01:

- links relativos existentes;
- numeração 15–20 contínua;
- termos `taxa`, `PoissonRate`, `PricingRequest` e `PricingResult` coerentes;
- estados aprovado, observado, recomendado e pendente separados;
- nenhum arquivo 01–14 ou ADR alterado;
- nenhum arquivo em `packages/pricing-engine/` alterado;
- nenhum código, dependência, fixture privada ou artefato temporário;
- `git diff --check` aprovado.

## 11. Decisão final histórica da T01

**T01 DOCUMENTAL PLANEJADA E VALIDÁVEL.**

**NO-GO PARA IMPLEMENTAÇÃO MATEMÁTICA E PARA INÍCIO DA T02.**

Naquele momento, o encerramento documental não implicava aprovação das sete
decisões pendentes.

## 12. Reavaliação após aprovação do Product Owner

### 12.1 Estado verificado

- `LVFI-ENG-003-T01` publicada no commit
  `18be07dd1a32957039a275b6b7fd216fc92c74a5`;
- aprovação explícita posterior das decisões `D-M1-001` a `D-M1-007`;
- Company Context, Development Framework, `D-MATH-001` a `D-MATH-016` e
  `ADR-LVFI-001` a `ADR-LVFI-010` revisados;
- nenhum conflito normativo ou necessidade de novo ADR;
- Pricing Engine `1.0.0`, schemas v1 e hashes preservados.

### 12.2 Decisões e encerramento das pendências

| Pendência histórica | Decisão aprovada | Resultado |
|---|---|---|
| `M1-PEND-001` | `D-M1-001` — fórmula canônica | Encerrada |
| `M1-PEND-002` | `D-M1-002` — pesos `0.50/0.50` | Encerrada |
| `M1-PEND-003` | `D-M1-003` — `uniform/v1` | Encerrada |
| `M1-PEND-004` | `D-M1-004` — composição multiplicativa | Encerrada |
| `M1-PEND-005` | `D-M1-005` — gols FT e 1T | Encerrada |
| `M1-PEND-006` | `D-M1-006` — assimetria e qualidade | Encerrada |
| `M1-PEND-007` | `D-M1-007` — estados especiais | Encerrada |

As regras completas e normativas estão no
[documento 17](17-method-one-mathematical-decisions.md). Os documentos de plano,
contratos, testes e backlog foram reconciliados com as decisões.

### 12.3 Novo gate

**GO PARA PLANEJAMENTO DA LVFI-ENG-003-T02.**

Esse GO encerra o bloqueio decisório da T01, mas não autoriza implementação nem
início da T02. A T02 continua dependente de plano próprio, aprovação explícita
e gates específicos. T03 e todas as etapas matemáticas posteriores permanecem
fora do escopo deste gate.

## 13. Referências

- [Plano técnico do Método 1](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Decisões matemáticas e pendências](17-method-one-mathematical-decisions.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog de implementação](19-method-one-implementation-backlog.md)
- [Validação final do Pricing Engine](14-pricing-engine-final-validation.md)
