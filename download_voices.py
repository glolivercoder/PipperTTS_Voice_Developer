#!/usr/bin/env python3
"""
Script para baixar modelos de voz pré-treinados do Piper TTS
"""

import os
import json
import requests
import gdown
from pathlib import Path

def download_file(url, output_path):
    """Baixa arquivo de URL ou Google Drive"""
    try:
        if 'drive.google.com' in url or 'googleusercontent.com' in url:
            # Usar gdown para Google Drive
            gdown.download(url, str(output_path), quiet=False)
        else:
            # Download direto
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        return True
    except Exception as e:
        print(f"❌ Erro ao baixar {url}: {e}")
        return False

def download_pretrained_models():
    """Baixa modelos pré-treinados populares"""
    
    # Modelos a serem baixados
    models_to_download = {
        'faber_pt_br': {
            'name': 'Faber (Português Brasil)',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx',
            'config_url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json',
            'language': 'pt'
        },
        'amy_en_us': {
            'name': 'Amy (Inglês EUA)',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx',
            'config_url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json',
            'language': 'en'
        },
        'lessac_en_us': {
            'name': 'Lessac (Inglês EUA)',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx',
            'config_url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json',
            'language': 'en'
        }
    }
    
    models_dir = Path('trained_models')
    models_dir.mkdir(exist_ok=True)
    
    downloaded_models = []
    
    for model_key, model_info in models_to_download.items():
        print(f"\n📥 Baixando modelo: {model_info['name']}")
        
        model_dir = models_dir / model_key
        model_dir.mkdir(exist_ok=True)
        
        # Baixar modelo ONNX
        model_path = model_dir / f"{model_key}.onnx"
        config_path = model_dir / f"{model_key}.onnx.json"
        
        success_model = download_file(model_info['url'], model_path)
        success_config = download_file(model_info['config_url'], config_path)
        
        if success_model and success_config:
            print(f"✅ Modelo {model_info['name']} baixado com sucesso!")
            downloaded_models.append({
                'key': model_key,
                'name': model_info['name'],
                'language': model_info['language'],
                'path': str(model_dir)
            })
        else:
            print(f"❌ Falha ao baixar {model_info['name']}")
            # Limpar arquivos parciais
            if model_path.exists():
                model_path.unlink()
            if config_path.exists():
                config_path.unlink()
    
    return downloaded_models

def main():
    """Função principal"""
    print("🚀 Iniciando download de modelos de voz pré-treinados...")
    
    downloaded = download_pretrained_models()
    
    if downloaded:
        print(f"\n✅ {len(downloaded)} modelos baixados com sucesso:")
        for model in downloaded:
            print(f"   - {model['name']} ({model['language']})")
        
        print(f"\n📁 Modelos salvos em: trained_models/")
        print("\n🌐 Acesse http://localhost:5000 para usar os modelos!")
    else:
        print("\n❌ Nenhum modelo foi baixado.")

if __name__ == "__main__":
    main()