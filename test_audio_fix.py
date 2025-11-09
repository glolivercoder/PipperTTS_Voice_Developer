#!/usr/bin/env python3
"""
Script de teste para verificar e corrigir problemas de geração de áudio
"""
import os
import json
import requests
import subprocess
import time

def test_audio_generation():
    """Testa a geração de áudio com os modelos disponíveis"""
    
    print("🧪 Iniciando teste de geração de áudio...")
    
    # Testar cada modelo disponível
    models_dir = "trained_models"
    test_passed = []
    test_failed = []
    
    if not os.path.exists(models_dir):
        print("❌ Diretório de modelos não encontrado!")
        return
    
    models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
    
    if not models:
        print("❌ Nenhum modelo encontrado!")
        return
    
    print(f"📋 Encontrados {len(models)} modelos para testar")
    
    # Criar diretório de teste
    os.makedirs("static/audio/test", exist_ok=True)
    
    for model_name in models:
        print(f"\n🎤 Testando modelo: {model_name}")
        
        try:
            # Preparar dados para teste
            test_data = {
                "model_name": model_name,
                "text": "Este é um teste de geração de áudio."
            }
            
            # Fazer requisição ao servidor local
            response = requests.post(
                "http://localhost:5000/test_voice",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ {model_name}: SUCESSO")
                    print(f"   📁 Áudio gerado: {result.get('audio_url')}")
                    print(f"   💬 Mensagem: {result.get('message')}")
                    test_passed.append(model_name)
                else:
                    print(f"❌ {model_name}: FALHA - {result.get('error')}")
                    test_failed.append(model_name)
            else:
                print(f"❌ {model_name}: HTTP {response.status_code}")
                test_failed.append(model_name)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {model_name}: Erro de conexão - {e}")
            test_failed.append(model_name)
        except Exception as e:
            print(f"❌ {model_name}: Erro inesperado - {e}")
            test_failed.append(model_name)
    
    # Relatório final
    print(f"\n📊 RELATÓRIO DE TESTES:")
    print(f"✅ Modelos funcionando: {len(test_passed)}")
    for model in test_passed:
        print(f"   ✓ {model}")
    
    print(f"❌ Modelos com problemas: {len(test_failed)}")
    for model in test_failed:
        print(f"   ✗ {model}")
    
    # Verificar servidor
    try:
        response = requests.get("http://localhost:5000/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            print(f"\n📋 Modelos disponíveis no servidor: {len(models_data)}")
            for model in models_data:
                print(f"   📁 {model['name']} - ONNX: {model['has_onnx']}, JSON: {model['has_json']}")
    except:
        print("⚠️  Não foi possível verificar modelos no servidor")

def test_transcription_engines():
    """Testa os engines de transcrição"""
    print("\n🎤 Testando engines de transcrição...")
    
    try:
        response = requests.get("http://localhost:5000/transcription_engines", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Engines disponíveis: {data.get('engines', [])}")
            print(f"🎯 Engine padrão: {data.get('default')}")
        else:
            print(f"❌ Erro ao carregar engines: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🔧 Testando sistema Piper TTS")
    print("=" * 50)
    
    # Aguardar servidor iniciar
    print("⏳ Aguardando servidor iniciar...")
    time.sleep(2)
    
    # Testar conexão com servidor
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor web está rodando")
        else:
            print(f"⚠️  Servidor respondeu com status: {response.status_code}")
    except:
        print("❌ Servidor não está acessível. Inicie com: python web_interface.py")
        exit(1)
    
    # Executar testes
    test_audio_generation()
    test_transcription_engines()
    
    print("\n🎉 Teste concluído!")
    print("💡 Verifique os arquivos em static/audio/ para confirmar a geração")