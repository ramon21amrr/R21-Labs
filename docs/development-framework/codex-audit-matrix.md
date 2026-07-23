# Matriz de auditoria do Codex

O Codex protege marcos críticos; não é etapa obrigatória de toda tarefa. A
classificação considera impacto público, irreversibilidade, segurança,
matemática e capacidade de reproduzir resultados.

## Auditoria obrigatória

| Marco | Evidência mínima |
|---|---|
| Fechamento do Método 1 | escopo T02–T10, contratos, gates e readiness |
| Mudança matemática | decisão aprovada, ADR, propriedades e regressões |
| Schema ou contrato público | compatibilidade, versionamento e consumidor |
| Serialização ou hash | bytes canônicos, versões, fixtures e determinismo |
| Banco ou migração | plano de migração/rollback, integridade e backup |
| Autenticação ou segurança | threat model, segredos, permissões e testes |
| Integração externa crítica | contrato, falhas, privacidade e observabilidade |
| Release | versões, wheel, instalação limpa, hashes e documentação |
| Piloto | critérios de entrada/saída, dados, segurança e rollback |
| Pré-comercialização | readiness técnica, operacional, legal e de suporte |

A auditoria é somente revisão e evidência; não transfere aceite, merge ou release
do Product Owner.

## Auditoria opcional

| Trabalho | Condição para permanecer opcional |
|---|---|
| Documentação | não muda política, contrato, segurança ou matemática |
| Teste simples | não altera expectativa pública nem mascara regressão |
| Estilo/formatação | sem mudança semântica |
| Componente visual pequeno | sem contrato, autenticação ou dado sensível |
| Refatoração local | comportamento e interface públicos preservados |

Eleve uma tarefa opcional para obrigatória se o diff revelar impacto em schema,
hash, versão, segurança, persistência, integração crítica ou matemática, se os
gates divergirem, ou se houver conflito documental.

## Registro

O relatório da tarefa registra: classificação; justificativa; artefatos
revisados; achados; gates; decisão; riscos residuais; e ação do Product Owner.
Ausência de achados não substitui execução dos gates.
