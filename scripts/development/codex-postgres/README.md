# Scripts do PostgreSQL persistente do Codex

Consulte `docs/development-framework/codex-postgres-test-environment.md`. Scripts
normais não recebem senha por parâmetro, não gravam conexão em arquivo e só usam a
role `codex_test` no loopback `127.0.0.1:55432`.

- `Install-CodexPostgresTestEnvironment.ps1`: única operação elevada; cria ou
  reconcilia cluster, credenciais e tarefa agendada sob o usuário do Codex.
- `Get-CodexPostgresTestEnvironment.ps1`: status sem segredo.
- `New-CodexPostgresTaskDatabase.ps1`: cria banco `codex_task_*` como `codex_test`.
- `Invoke-CodexPostgresTask.ps1`: migrations, downgrade opcional e testes.
- `Clear-CodexPostgresFailedTask.ps1` e `Remove-CodexPostgresTaskDatabase.ps1`:
  encerram sessões e removem somente banco validado.
- `Test-CodexPostgresTestEnvironment.ps1`: validação de ponta a ponta.
- `Uninstall-CodexPostgresTestEnvironment.ps1`: rollback elevado e explícito.
