#!/usr/bin/env python3
"""Script para testar os modelos de voz"""

import requests
import json
import time

def test_model(model_name, text, language):
    """Testa um modelo de voz específico"""
    print(f"\n🎯 Testando {model_name} ({language})...")
    print(f"Texto: '{text}'")
    
    try:
        response = requests.post(
            'http://localhost:5000/test_voice',
            json={'model_name': model_name, 'text': text},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            audio_url = result.get('audio_url', 'Sem URL')
            message = result.get('message', 'Sem mensagem')
            success = result.get('success', False)
            
            print(f"✅ Sucesso: {success}")
            print(f"📍 URL do áudio: {audio_url}")
            print(f"💬 Mensagem: {message}")
            return True
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        return False
    except requests.exceptions.Timeout:
        print("❌ Erro: Tempo limite excedido")
        return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes dos modelos de voz...")
    
    # Aguardar um momento para a aplicação estar pronta
    time.sleep(2)
    
    # Testes dos modelos
    test_cases = [
        ('faber_pt_br', 'Olá! Este é um teste do modelo Faber em português.', 'Português Brasil'),
        ('amy_en_us', 'Hello! This is a test of the Amy model in English.', 'Inglês EUA'),
        ('lessac_en_us', 'Hello! This is a test of the Lessac model in English.', 'Inglês EUA'),
        ('voz_teste', 'Olá! Este é um teste da voz de teste.', 'Teste')
    ]
    
    results = []
    for model_name, text, language in test_cases:
        success = test_model(model_name, text, language)
        results.append((model_name, success))
        time.sleep(1)  # Pequena pausa entre testes
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    for model_name, success in results:
        status = "✅ OK" if success else "❌ FALHOU"
        print(f"{model_name}: {status}")
    
    working_models = [name for name, success in results if success]
    failed_models = [name for name, success in results if not success]
    
    print(f"\n✅ Modelos funcionando: {len(working_models)}")
    print(f"❌ Modelos com falha: {len(failed_models)}")
    
    if working_models:
        print(f"\n🎉 Os seguintes modelos estão funcionando: {', '.join(working_models)}")
    
    if failed_models:
        print(f"\n⚠️  Os seguintes modelos apresentaram problemas: {', '.join(failed_models)}")

if __name__ == "__main__":
    main()