# Script gerado pelo Claude Orchestrator. Roda uma sessão autônoma.
$ErrorActionPreference = 'Continue'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$projectPath = 'C:\Outros\Cravo'
$promptFile  = 'C:\Outros\Cravo\.agent\sessions\20260512_221710_cbcfb4ca.prompt.txt'
$logFile     = 'C:\Outros\Cravo\.agent\sessions\20260512_221710_cbcfb4ca.log'
Set-Location -LiteralPath $projectPath
Write-Host '== Claude Orchestrator — sessão autônoma ==' -ForegroundColor Cyan
Write-Host "Projeto:  $projectPath"
Write-Host "Log:      $logFile"
Write-Host "Prompt:   $promptFile"
Write-Host ''
$prompt = Get-Content -Raw -LiteralPath $promptFile
claude --dangerously-skip-permissions $prompt 2>&1 | Tee-Object -FilePath $logFile
Write-Host ''
Write-Host '== Sessão encerrada. Pressione Enter pra fechar a janela ==' -ForegroundColor Yellow
Read-Host | Out-Null
