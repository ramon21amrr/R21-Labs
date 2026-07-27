# R21 Labs

Siga: instrução explícita mais recente do Product Owner; task; contexto da
empresa; framework; documentação do produto; ADRs; código e testes. Em conflito,
pare, registre as fontes e peça decisão.

Antes de mudar: confirme baseline, branch própria, escopo, ambiente autorizado e
gates. Para localização, arquitetura ou impacto, consulte primeiro
`graphify-out/graph.json` com consulta limitada quando existir; abra só as fontes
indicadas e confirme toda decisão material no original. Se o grafo estiver ausente,
desatualizado ou insuficiente, use busca direcionada e informe-o.

Não leia relatórios do grafo integralmente por padrão, não trate relações inferidas
como prova e não inicie outra task. Preserve contratos, schemas, hashes, fixtures,
testes, cobertura, versões e matemática congelada. Não leia segredos nem altere
produto fora do escopo.

Nunca trabalhe diretamente em `main`, force-push, reescreva histórico, use
`reset --hard` ou `git clean` amplo, instale dependência global, nem altere lock
sem escopo explícito. Publicação exige a autorização e o fluxo do framework.

Use Skills versionadas em `.agents/skills/` conforme a descrição; procedimentos e
gates detalhados ficam nelas. Antes da entrega, revise diff e escopo, faça varredura
de segredos, execute `git diff --check`, rode gates aplicáveis e apresente ao
Product Owner resultado, evidências, limitações e próxima ação humana, se houver.