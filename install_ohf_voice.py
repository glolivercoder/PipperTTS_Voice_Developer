#!/usr/bin/env python3
"""
Script para migrar para o repositório OHF-Voice/piper1-gpl
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
    print("🔄 Migrando para OHF-Voice/piper1-gpl...")
    
    # Verificar se existe o diretório piper antigo
    if os.path.exists("piper_old"):
        print("⚠️  Diretório piper_old já existe. Removendo...")
        shutil.rmtree("piper_old")
    
    # Fazer backup do repositório antigo
    if os.path.exists("src/python_run"):
        print("📦 Fazendo backup do repositório antigo...")
        shutil.move("src/python_run", "piper_old")
    
    # Clonar o novo repositório
    print("📥 Clonando OHF-Voice/piper1-gpl...")
    if not run_command("git clone https://github.com/OHF-Voice/piper1-gpl.git"):
        print("❌ Falha ao clonar o repositório")
        return False
    
    # Mover o novo código para src/python_run
    print("📂 Organizando estrutura...")
    if os.path.exists("piper1-gpl"):
        shutil.move("piper1-gpl", "src/piper_new")
    
    # Copiar arquivos importantes
    important_files = [
        "piper_old/setup.py",
        "piper_old/requirements.txt",
        "piper_old/requirements_dev.txt"
    ]
    
    for file in important_files:
        if os.path.exists(file):
            dest = file.replace("piper_old/", "src/piper_new/")
            if os.path.exists(dest):
                shutil.copy2(file, dest + ".backup")
                print(f"📝 Backup criado: {dest}.backup")
    
    print("✅ Migração concluída!")
    print("\n📋 Próximos passos:")
    print("1. Instale as novas dependências: pip install -e src/piper_new/")
    print("2. Teste a nova versão com seus modelos existentes")
    print("3. Se necessário, restaure o backup de src/piper_old/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)