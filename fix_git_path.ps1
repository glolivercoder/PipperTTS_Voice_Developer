# Script para corrigir o PATH do Git no Windows
# Execute este script como Administrador

Write-Host "=== Corrigindo PATH do Git ===" -ForegroundColor Green

# Verificar se o Git está instalado
$gitPath = "C:\Program Files\Git\cmd"
$gitExe = "$gitPath\git.exe"

if (Test-Path $gitExe) {
    Write-Host "Git encontrado em: $gitExe" -ForegroundColor Green
    
    # Obter o PATH atual do sistema
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    
    # Verificar se o Git já está no PATH
    if ($currentPath -like "*$gitPath*") {
        Write-Host "O Git já está no PATH do sistema!" -ForegroundColor Yellow
    } else {
        Write-Host "Adicionando Git ao PATH do sistema..." -ForegroundColor Yellow
        
        # Adicionar o Git ao PATH
        $newPath = $currentPath + ";" + $gitPath
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        
        Write-Host "Git adicionado ao PATH com sucesso!" -ForegroundColor Green
        Write-Host "Reinicie o terminal para aplicar as mudanças." -ForegroundColor Cyan
    }
    
    # Testar o Git
    Write-Host "Testando Git..." -ForegroundColor Yellow
    & $gitExe --version
    
} else {
    Write-Host "Git não encontrado em $gitExe" -ForegroundColor Red
    Write-Host "Por favor, instale o Git primeiro." -ForegroundColor Red
}

Write-Host "=== Processo concluído ===" -ForegroundColor Green