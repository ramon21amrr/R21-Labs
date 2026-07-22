# Gate de planejamento do Método 1

## 1. Identificação

- **Initiative:** `LVFI-ENG-003`
- **Task avaliada:** `LVFI-ENG-003-T01`
- **Componente futuro:** Método 1 — médias com contexto
- **Dependência aceita:** Pricing Engine `1.0.0`
- **Data do diagnóstico:** 2026-07-21

## 2. Resultado

**NO-GO PARA IMPLEMENTAÇÃO MATEMÁTICA DO MÉTODO 1.**

O planejamento técnico, o catálogo de contratos, a estratégia de testes e o
backlog estão definidos. Entretanto, sete decisões de produto e matemática
continuam sem aprovação explícita. A implementação não pode escolher essas
regras por inferência, conveniência técnica ou comportamento do legado.

Este gate não autoriza `LVFI-ENG-003-T02` nem qualquer alteração de código.

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

## 6. Pendências bloqueadoras

### 6.1 `M1-PEND-001` — fórmula canônica de combinação

Não há aprovação explícita da média aritmética ponderada como fórmula normativa.

**Necessário para liberar:** fórmula, versão e aplicabilidade aprovadas.

### 6.2 `M1-PEND-002` — pesos globais iniciais

O legado usa `0,5/0,5`, enquanto o exemplo documental usa `0,6/0,4`.

**Necessário para liberar:** valores ou política de configuração obrigatória.

### 6.3 `M1-PEND-003` — ausência de recência no MVP

Não existe fórmula de recência aprovada.

**Necessário para liberar:** aprovação da política uniforme ou especificação
completa de alternativa.

### 6.4 `M1-PEND-004` — composição dos multiplicadores

O produto simples é observado e recomendado, mas permanece pendente.

**Necessário para liberar:** fórmula, ordem e catálogo aplicável por estatística.

### 6.5 `M1-PEND-005` — escopo inicial de estatísticas e elegibilidade para Poisson

Não está aprovado quais estatísticas e períodos integram a primeira versão nem
quais podem virar `PoissonRate`.

**Necessário para liberar:** catálogo inicial e política de elegibilidade de
distribuição.

### 6.6 `M1-PEND-006` — aceitação de amostras assimétricas

O comportamento do Método 1 para tamanhos diferentes não está aprovado.

**Necessário para liberar:** aceitar, equalizar ou bloquear, incluindo warnings.

### 6.7 `M1-PEND-007` — política dos estados especiais de partida

Anuladas, interrompidas, W.O., prorrogação e pênaltis não possuem política
aprovada.

**Necessário para liberar:** elegibilidade por estado, período e estatística.

## 7. Recomendações não aprovadas

- média aritmética ponderada de produção e concessão;
- preset global neutro `0,5/0,5`;
- recência uniforme no MVP;
- produto ordenado dos multiplicadores;
- gols de primeiro tempo e tempo regulamentar como escopo inicial;
- Poisson somente para combinações explicitamente autorizadas;
- amostras assimétricas aceitas com denominadores separados e warning;
- somente partidas encerradas no tempo regulamentar na primeira política.

Essas recomendações permanecem sem efeito normativo.

## 8. Condições para novo gate

Um novo gate poderá ser solicitado quando:

1. o Product Owner decidir explicitamente os sete itens;
2. o documento 17 for atualizado com o estado aprovado e referência do aceite;
3. fórmula, configuração, schemas e testes forem reconciliados com as decisões;
4. o backlog for revisado se alguma escolha alterar contratos ou sequência;
5. a próxima Task possuir plano próprio aprovado.

Somente então poderá ser avaliado `GO`, `GO COM CONDIÇÕES` ou manutenção do
`NO-GO`.

## 9. Proibições durante o NO-GO

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

## 11. Decisão final da T01

**T01 DOCUMENTAL PLANEJADA E VALIDÁVEL.**

**NO-GO PARA IMPLEMENTAÇÃO MATEMÁTICA E PARA INÍCIO DA T02.**

O encerramento documental não implica aprovação das sete decisões pendentes.

## 12. Referências

- [Plano técnico do Método 1](15-method-one-technical-plan.md)
- [Catálogo de contratos](16-method-one-contract-catalog.md)
- [Decisões matemáticas e pendências](17-method-one-mathematical-decisions.md)
- [Estratégia de testes](18-method-one-test-strategy.md)
- [Backlog de implementação](19-method-one-implementation-backlog.md)
- [Validação final do Pricing Engine](14-pricing-engine-final-validation.md)
