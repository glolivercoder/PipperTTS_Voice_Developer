#!/usr/bin/env python3
"""Script para analisar os modelos de voz"""

import json
import os

def analyze_model(model_name):
    """Analisa um modelo específico"""
    config_path = f'trained_models/{model_name}/{model_name}.onnx.json'
    
    if not os.path.exists(config_path):
        print(f"❌ Arquivo não encontrado: {config_path}")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        phoneme_id_map = config.get('phoneme_id_map', {})
        
        # Encontrar ID máximo
        max_id = 0
        for phoneme, ids in phoneme_id_map.items():
            for id_val in ids:
                max_id = max(max_id, id_val)
        
        print(f"\n📊 Análise do modelo: {model_name}")
        print(f"   📍 Total de fonemas: {len(phoneme_id_map)}")
        print(f"   📈 ID máximo: {max_id}")
        print(f"   🔤 Tipo de fonema: {config.get('phoneme_type', 'desconhecido')}")
        print(f"   🗣️  Voz espeak: {config.get('espeak', {}).get('voice', 'não definida')}")
        
        # Verificar se há mapa de caracteres
        if 'phoneme_map' in config and config['phoneme_map']:
            print(f"   🗺️  Mapa de fonemas: {len(config['phoneme_map'])} entradas")
        
        return max_id
        
    except Exception as e:
        print(f"❌ Erro ao analisar {model_name}: {e}")
        return None

def main():
    """Função principal"""
    print("🔍 Analisando modelos de voz...")
    
    models = ['faber_pt_br', 'amy_en_us', 'lessac_en_us', 'voz_teste']
    
    max_ids = {}
    for model in models:
        max_id = analyze_model(model)
        if max_id is not None:
            max_ids[model] = max_id
    
    print("\n" + "="*50)
    print("📊 RESUMO DOS MODELOS")
    print("="*50)
    
    for model, max_id in max_ids.items():
        print(f"{model}: ID máximo = {max_id}")
    
    # Comparar com o que está funcionando
    if 'faber_pt_br' in max_ids:
        print(f"\n✅ Modelo de referência (faber_pt_br): ID máximo = {max_ids['faber_pt_br']}")
    
    print("\n💡 Dica: O erro 'indices element out of data bounds' indica que")
    print("   o modelo está tentando acessar um índice que não existe.")
    print("   Isso pode acontecer se o ID do fonema for maior que o esperado.")

if __name__ == "__main__":
    main()