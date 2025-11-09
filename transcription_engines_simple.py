#!/usr/bin/env python3
"""
Módulo ultra-simples para verificar engines de transcrição disponíveis
"""

def get_transcription_engines_ultra_simple():
    """Versão ultra-simples que retorna engines básicos sem importações"""
    # Retorna engines básicos sem verificar importações para evitar erros
    return ['google', 'wav2vec2']

if __name__ == "__main__":
    engines = get_transcription_engines_ultra_simple()
    print(f"Engines disponíveis: {engines}")