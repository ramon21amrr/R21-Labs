# LVFI ENG 005 Metodo 3 Frequencia Observada

## Autoridade e fronteira

O Product Owner autorizou nesta sessão a `LVFI-ENG-005` sobre a base
`9dc6bed0c8ef9303dccbf4f6ded5bd45294cc694`. Esta task entrega apenas o núcleo
determinístico, versionado e verificável do Método 3 sobre os contratos de
amostra somente leitura da APP-013. Não altera o Método 1 `1.0.0`, Pricing
Engine `1.0.1`, seus schemas, hashes, fixtures ou baselines; não inicia Método
2, ENG-006, Match Center, PDF, Value Tracker, oportunidades, staking ou
integrações com casas.

O contrato público é aditivo e não persiste execução. Uma rota de leitura só pode
ser exposta quando transportar este contrato sem alterar a API já publicada pela
APP-013.

## Fontes e regra matemática aprovada

O documento 39 exige frequência de mandante, visitante e combinada, ausência
distinta de zero, denominador composto somente por observações numéricas válidas
e corte temporal sem look-ahead. O material privado `METODOS E CALCULOS.docx`
foi usado somente após SHA-256
`A17074F736EE830F03DA5EB3ADAF12BBAA22DA0CFCCB3B3366FEA8AD0429FFD3`, igual ao
fingerprint registrado no documento 39. Ele descreve o modelo como soma das
frequências dos eventos: conta o evento nos últimos jogos de mandante e visitante
e divide pela quantidade de eventos observáveis. O XLSM local não coincidiu com o
fingerprint aprovado e não é usado.

Para cada lado `s` em `{home, away}`, seja `V_s` a sequência de valores numéricos
válidos da amostra da APP-013 e `A_s` os que satisfazem o comparador e alvo
explícitos. A frequência é `f_s = |A_s| / |V_s|` quando `|V_s| > 0`; caso
contrário é indisponível (`null`). Zero é numérico e participa de `V_s`.

A frequência combinada é a soma de eventos dos dois lados sobre a soma dos
denominadores válidos: `f_combined = (|A_home| + |A_away|) /
(|V_home| + |V_away|)`, quando este denominador é positivo; caso contrário é
indisponível. Isto preserva a paridade conceitual da soma de frequências sem
transformar ausência em zero ou aplicar média não ponderada de percentuais.

## Configuração e resultado versionados

`method` é sempre `method_three_observed_frequency` e `method_version` é
`1.0.0`. A configuração explícita contém tamanho nominal `5`, `10`, `15` ou
`20`, escopo de competição, escopo e ID da temporada anterior quando aplicável,
métrica, comparador e alvo. O mandante usa a amostra `home` do participante
mandante e o visitante a amostra `away` do participante visitante. Cada amostra
é a resposta existente da APP-013, inclusive ordenação determinística
`played_on_desc_match_id_asc`, corte estrito por data e `match_id`, valores,
ausências, IDs candidatos/usados e warnings.

O resultado identifica método, versão, configuração, match alvo, três
frequências, tamanho nominal, denominadores efetivamente válidos, quantidades de
eventos, amostras reais, partidas usadas e warnings. Ele agrega os warnings das
duas amostras com prefixo de lado e acrescenta indisponibilidade explícita para
um lado sem observações válidas ou para combinado sem denominador. Nenhuma
observação posterior ao cutoff pode integrar o resultado.

## Aceite verificável

- Mandante, visitante e combinado seguem as fórmulas acima.
- Ausências são excluídas; zero válido entra no denominador.
- Amostra parcial e vazia são retornadas com warnings, sem fallback silencioso.
- Os tamanhos 5, 10, 15 e 20 preservam a mesma semântica da APP-013.
- A ordem, o cutoff, os IDs usados e o resultado são determinísticos.
- Fixtures sanitizadas podem verificar a fórmula; nenhuma fixture ou arquivo
  privado completo é versionado.
