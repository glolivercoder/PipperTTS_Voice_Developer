#!/usr/bin/env python3
"""
Teste rápido e simples dos modelos de voz Piper TTS.
Verifica se cada modelo consegue gerar áudio básico.
"""

import requests
import json
import time
import os

def quick_test():
    """Teste rápido de cada modelo com timeout curto."""
    
    base_url = "http://localhost:5000"
    
    # Textos simples para teste rápido
    test_cases = [
        ("faber_pt_br", "Olá"),
        ("amy_en_us", "Hello"),
        ("lessac_en_us", "Hello"),
        ("voz_teste", "Teste")
    ]
    
    print("⚡ Teste rápido dos modelos Piper TTS")
    print("=" * 40)
    
    working_models = []
    failed_models = []
    
    for model_name, text in test_cases:
        print(f"\n🎯 Testando {model_name}...")
        
        try:
            # Teste com timeout de 10 segundos
            response = requests.post(
                f"{base_url}/test_voice",
                json={"model_name": model_name, "text": text},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    audio_url = result.get('audio_url')
                    print(f"  ✅ SUCESSO - {audio_url}")
                    working_models.append(model_name)
                else:
                    print(f"  ❌ FALHA - {result.get('error', 'Erro desconhecido')}")
                    failed_models.append(model_name)
            else:
                print(f"  ❌ FALHA - HTTP {response.status_code}")
                failed_models.append(model_name)
                
        except requests.exceptions.Timeout:
            print(f"  ❌ TIMEOUT - Modelo muito lento")
            failed_models.append(model_name)
            
        except Exception as e:
            print(f"  ❌ ERRO - {str(e)}")
            failed_models.append(model_name)
        
        # Pequena pausa entre testes
        time.sleep(0.5)
    
    # Resumo
    print(f"\n{'='*40}")
    print("📊 RESUMO RÁPIDO:")
    print(f"✅ Modelos funcionando: {len(working_models)}")
    print(f"❌ Modelos com falha: {len(failed_models)}")
    
    if working_models:
        print(f"\n🎉 Modelos OK: {', '.join(working_models)}")
    
    if failed_models:
        print(f"⚠️  Modelos com problemas: {', '.join(failed_models)}")
        print("\n💡 Dicas:")
        print("   - Verifique se os arquivos .onnx estão corretos")
        print("   - Confira as configurações nos arquivos .json")
        print("   - Os modelos podem estar demorando muito para carregar")

if __name__ == "__main__":
    try:
        # Verificar se servidor está respondendo
        response = requests.get("http://localhost:5000/models", timeout=5)
        if response.status_code == 200:
            quick_test()
        else:
            print("❌ Servidor não está respondendo corretamente.")
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor.")
        print("💡 Certifique-se de que a aplicação web está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro ao conectar ao servidor: {e}")