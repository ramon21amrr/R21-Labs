# Publicação manual segura

Use somente após gates aprovados e autorização explícita. Confirme branch não-main,
árvore limpa, parent autorizado, commit único, PR aberto/limpo/mergeable e checks
aprovados. Faça push apenas da branch, crie PR para `main`, use merge commit quando
aprovado e sincronize `main` com fast-forward only. Pare em qualquer ambiguidade;
nunca force-push, publique diretamente em `main` ou apague a branch automaticamente.