#!/usr/bin/env python3
"""
Script para migrar para o repositório glolivercoder/PipperTTS_Voice_Developer
"""

import os
import subprocess
import sys
import shutil

def run_command(cmd, cwd=None):
    """Executa um comando e retorna o resultado"""
    print(f"Executando: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erro: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    """Função principal de migração"""
    print("🔄 Migrando para glolivercoder/PipperTTS_Voice_Developer...")
    
    # Verificar se existe o diretório piper antigo
    if os.path.exists("piper_old_fork"):
        print("⚠️  Diretório piper_old_fork já existe. Removendo...")
        shutil.rmtree("piper_old_fork")
    
    # Fazer backup do repositório antigo
    if os.path.exists("src/piper_new"):
        print("📦 Fazendo backup do repositório antigo...")
        shutil.move("src/piper_new", "piper_old_fork")
    
    # Clonar o novo repositório
    print("📥 Clonando glolivercoder/PipperTTS_Voice_Developer...")
    if not run_command("git clone https://github.com/glolivercoder/PipperTTS_Voice_Developer.git"):
        print("❌ Falha ao clonar o repositório")
        return False
    
    print("✅ Migração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Navegue até o diretório 'PipperTTS_Voice_Developer'")
    print("2. Siga as instruções do README.md para instalar as dependências e executar o projeto.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)