# LVFI-APP-018 — PDF-resumo e operação local

## Contrato aprovado

O relatório é uma projeção HTML/CSS convertida em PDF por Chromium/Playwright no
servidor. Ele recebe exclusivamente um `AnalysisSnapshot` já aprovado pela
APP-015: não consulta dados, configurações, amostras ou resultados mutáveis e
nunca executa cálculo de domínio. O template versionado produz identificação,
resumo/resultados persistidos, metodologia, versões, filtros, amostras,
warnings e responsável. Cada artefato registra SHA-256, versão do template,
snapshot e localização; é append-only e retido enquanto o snapshot existir.

O operador deve fornecer `LVFI_PDF_STORAGE_DIR`; não há exclusão automática.
PDFs, banco, metadados e a configuração operacional entram no backup. Caches,
logs, builds e sessões ficam fora do conjunto de recuperação.

## Operação e recuperação

Os scripts locais iniciam/paralisam a API e web, validam `/health` e `/ready`,
e geram backups fora do diretório de dados ativo. O agendamento diário, backup
manual antes de migration/upgrade e a retenção de 14 diários, 8 semanais e 6
mensais são controlados pelo operador local. O manifesto contém hashes SHA-256.

O ensaio de recuperação restaura PostgreSQL, PDFs, metadados e configuração em
ambiente descartável; valida hashes, inicia a aplicação, consulta readiness e
um snapshot aprovado/PDF, então remove o ambiente. RPO contratado: 24 horas;
RTO contratado: 2 horas. Cloud, replicação externa, piloto e múltiplos usuários
permanecem fora de escopo.
