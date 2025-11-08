#!/usr/bin/env python3
"""
Script para testar todos os modelos de voz com diferentes textos
e verificar se estão gerando áudio corretamente.
"""

import requests
import json
import time
import os
from pathlib import Path

def test_all_models():
    """Testa todos os modelos disponíveis com textos apropriados."""
    
    # URL base da API
    base_url = "http://localhost:5000"
    
    # Textos de teste para diferentes idiomas
    test_texts = {
        "faber_pt_br": [
            "Olá! Este é um teste do modelo Faber em português.",
            "Como você está hoje?",
            "Testando síntese de voz em português do Brasil."
        ],
        "amy_en_us": [
            "Hello! This is a test of the Amy model in English.",
            "How are you today?",
            "Testing speech synthesis in American English."
        ],
        "lessac_en_us": [
            "Hello! This is a test of the Lessac model in English.",
            "The quick brown fox jumps over the lazy dog.",
            "Testing speech synthesis with the Lessac voice."
        ],
        "voz_teste": [
            "Olá! Este é um teste da voz de teste.",
            "Testando modelo de voz personalizado.",
            "Síntese de voz funcionando corretamente."
        ]
    }
    
    print("🧪 Iniciando testes completos dos modelos de voz...")
    print("=" * 60)
    
    # Primeiro, obter lista de modelos disponíveis
    try:
        response = requests.get(f"{base_url}/models")
        models = response.json()
        print(f"📋 Modelos encontrados: {len(models)}")
        for model in models:
            print(f"   - {model['name']}")
        print()
    except Exception as e:
        print(f"❌ Erro ao obter lista de modelos: {e}")
        return
    
    # Testar cada modelo
    resultados = {}
    total_tests = 0
    passed_tests = 0
    
    for model_info in models:
        model_name = model_info['name']
        print(f"\n🎯 Testando modelo: {model_name}")
        print("-" * 40)
        
        if model_name not in test_texts:
            print(f"⚠️  Textos de teste não definidos para {model_name}")
            continue
        
        resultados[model_name] = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # Testar cada texto
        for i, text in enumerate(test_texts[model_name], 1):
            total_tests += 1
            resultados[model_name]['total'] += 1
            
            print(f"\n  Teste {i}: {text}")
            
            try:
                # Fazer requisição para gerar áudio
                response = requests.post(
                    f"{base_url}/test_voice",
                    json={"model_name": model_name, "text": text},
                    timeout=30  # Timeout de 30 segundos
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        audio_url = result.get('audio_url')
                        audio_path = f"static/audio/{os.path.basename(audio_url)}"
                        
                        # Verificar se o arquivo de áudio foi criado
                        if os.path.exists(audio_path):
                            file_size = os.path.getsize(audio_path)
                            print(f"  ✅ SUCESSO - Áudio gerado: {audio_url} ({file_size} bytes)")
                            resultados[model_name]['passed'] += 1
                            passed_tests += 1
                        else:
                            print(f"  ❌ FALHA - Arquivo de áudio não encontrado: {audio_path}")
                            resultados[model_name]['failed'] += 1
                            resultados[model_name]['errors'].append(f"Arquivo não encontrado: {audio_path}")
                    else:
                        print(f"  ❌ FALHA - API retornou erro: {result.get('error', 'Erro desconhecido')}")
                        resultados[model_name]['failed'] += 1
                        resultados[model_name]['errors'].append(f"API error: {result.get('error', 'Erro desconhecido')}")
                else:
                    print(f"  ❌ FALHA - Status HTTP: {response.status_code}")
                    resultados[model_name]['failed'] += 1
                    resultados[model_name]['errors'].append(f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ FALHA - Tempo limite excedido (30s)")
                resultados[model_name]['failed'] += 1
                resultados[model_name]['errors'].append("Timeout")
                
            except Exception as e:
                print(f"  ❌ FALHA - Erro: {str(e)}")
                resultados[model_name]['failed'] += 1
                resultados[model_name]['errors'].append(str(e))
            
            # Pequena pausa entre testes
            time.sleep(0.5)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    for model_name, stats in resultados.items():
        status = "✅ FUNCIONANDO" if stats['passed'] > 0 else "❌ COM PROBLEMAS"
        print(f"\n{model_name}: {status}")
        print(f"  Total de testes: {stats['total']}")
        print(f"  Aprovados: {stats['passed']}")
        print(f"  Falhados: {stats['failed']}")
        
        if stats['errors']:
            print(f"  Erros:")
            for error in stats['errors'][:3]:  # Mostrar até 3 erros
                print(f"    - {error}")
            if len(stats['errors']) > 3:
                print(f"    ... e mais {len(stats['errors']) - 3} erros")
    
    print(f"\n{'='*60}")
    print(f"📈 TOTAL GERAL:")
    print(f"  Testes realizados: {total_tests}")
    print(f"  Testes aprovados: {passed_tests}")
    print(f"  Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 Todos os modelos estão funcionando perfeitamente!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} testes falharam. Verifique os logs acima.")

if __name__ == "__main__":
    # Verificar se o servidor está rodando
    try:
        response = requests.get("http://localhost:5000/models", timeout=5)
        if response.status_code == 200:
            test_all_models()
        else:
            print("❌ Servidor não está respondendo corretamente.")
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor.")
        print("💡 Certifique-se de que a aplicação web está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro ao conectar ao servidor: {e}")