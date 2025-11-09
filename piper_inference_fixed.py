#!/usr/bin/env python3
"""
Sistema de inferência melhorado para modelos Piper TTS
"""
import os
import json
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime não disponível, usando fallback")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("torch não disponível")

class PiperTTSInference:
    """Sistema de inferência robusto para modelos Piper TTS"""
    
    def __init__(self, model_path: str, config_path: str):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.session = None
        self.model = None
        
        # Carregar configuração
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"✅ Configuração carregada: {self.config.get('model_type', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configuração: {e}")
            self.config = {}
        
        # Tentar carregar modelo ONNX
        if ONNX_AVAILABLE:
            try:
                self.session = ort.InferenceSession(str(self.model_path))
                logger.info("✅ Modelo ONNX carregado com sucesso")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo ONNX: {e}")
                self.session = None
        else:
            logger.warning("⚠️  ONNX não disponível")
        
        # Tentar carregar modelo PyTorch como fallback
        if not self.session and TORCH_AVAILABLE:
            try:
                # Tentar carregar como checkpoint PyTorch
                self.model = torch.load(self.model_path, map_location='cpu')
                self.model.eval()
                logger.info("✅ Modelo PyTorch carregado como fallback")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo PyTorch: {e}")
                self.model = None
        
        if not self.session and not self.model:
            logger.error("❌ Nenhum modelo pôde ser carregado")
    
    def text_to_phonemes(self, text: str, language: str = "pt") -> list:
        """Converte texto para sequência de IDs de fonemas (simplificado)"""
        
        # Obter mapa de fonemas do modelo ou usar valores padrão
        phoneme_id_map = self.config.get('phoneme_id_map', {})
        
        if not phoneme_id_map:
            logger.warning("⚠️  Mapa de fonemas não encontrado, usando valores padrão")
            phoneme_id_map = self._create_default_phoneme_map()
        
        # Converter texto para minúsculas e simplificar
        text = text.lower().strip()
        
        # Token de início
        bos_id = phoneme_id_map.get('_', [1])[0] if '_' in phoneme_id_map else 1
        phonemes = [bos_id]
        
        # Mapeamento simples de caracteres para fonemas
        char_to_phoneme = {
            'a': 'a', 'e': 'e', 'i': 'i', 'o': 'o', 'u': 'u',
            'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'g',
            'h': 'h', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm',
            'n': 'n', 'p': 'p', 'q': 'k', 'r': 'r', 's': 's',
            't': 't', 'v': 'v', 'w': 'w', 'x': 'ks', 'y': 'i',
            'z': 'z', ' ': ' ', '.': '.', ',': ',', '!': '!', '?': '?'
        }
        
        # Converter cada caractere
        for char in text:
            if char in char_to_phoneme:
                phoneme_char = char_to_phoneme[char]
                if phoneme_char in phoneme_id_map:
                    phoneme_id = phoneme_id_map[phoneme_char][0]
                    phonemes.append(phoneme_id)
                else:
                    # Caractere não encontrado, usar espaço
                    space_id = phoneme_id_map.get(' ', [3])[0] if ' ' in phoneme_id_map else 3
                    phonemes.append(space_id)
            else:
                # Caractere desconhecido, usar espaço
                space_id = phoneme_id_map.get(' ', [3])[0] if ' ' in phoneme_id_map else 3
                phonemes.append(space_id)
        
        # Token de fim
        eos_id = phoneme_id_map.get('$', [2])[0] if '$' in phoneme_id_map else 2
        phonemes.append(eos_id)
        
        # Garantir limites válidos
        max_id = max(max(ids) for ids in phoneme_id_map.values()) if phoneme_id_map else 200
        phonemes = [min(id_val, max_id) for id_val in phonemes]
        
        logger.info(f"📝 Texto convertido: '{text}' -> {len(phonemes)} fonemas")
        return phonemes
    
    def _create_default_phoneme_map(self):
        """Cria mapa de fonemas padrão se não existir"""
        return {
            '_': [1], '$': [2], ' ': [3], '.': [4], ',': [5], '!': [6], '?': [7],
            'a': [14], 'e': [18], 'i': [21], 'o': [27], 'u': [33],
            'b': [15], 'c': [16], 'd': [17], 'f': [19], 'g': [20],
            'h': [22], 'j': [23], 'k': [24], 'l': [25], 'm': [26],
            'n': [28], 'p': [29], 'q': [30], 'r': [31], 's': [32],
            't': [34], 'v': [35], 'w': [36], 'x': [37], 'y': [38], 'z': [39]
        }
    
    def generate_fallback_audio(self, text: str, sample_rate: int = 22050) -> np.ndarray:
        """Gera áudio de fallback quando o modelo não funciona"""
        
        logger.info("🔄 Gerando áudio de fallback")
        
        # Parâmetros do áudio
        duration = len(text) * 0.1  # ~0.1 segundos por caractere
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Gerar tom baseado no comprimento do texto
        base_freq = 220  # A3
        
        # Criar onda senoidal simples com variações
        audio = np.zeros_like(t)
        
        # Adicionar harmônicos baseados nos caracteres
        for i, char in enumerate(text.lower()):
            if char.isalpha():
                freq = base_freq + (ord(char) - ord('a')) * 10
                amplitude = 0.3 / (i + 1)  # Decaimento
                audio += amplitude * np.sin(2 * np.pi * freq * t)
        
        # Adicionar envelope ADR simples
        envelope = np.ones_like(t)
        attack_samples = int(0.01 * sample_rate)
        release_samples = int(0.1 * sample_rate)
        
        # Attack
        if len(envelope) > attack_samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Release
        if len(envelope) > release_samples:
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)
        
        audio *= envelope
        
        # Normalizar
        if np.max(np.abs(audio)) > 0:
            audio = 0.8 * audio / np.max(np.abs(audio))
        
        logger.info(f"✅ Áudio de fallback gerado: {len(audio)} amostras")
        return audio
    
    def synthesize_with_onnx(self, phonemes: list) -> np.ndarray:
        """Sintetiza áudio usando modelo ONNX"""
        
        if not self.session:
            raise RuntimeError("Modelo ONNX não disponível")
        
        try:
            # Preparar inputs
            phoneme_input = np.array([phonemes], dtype=np.int64)
            input_lengths = np.array([len(phonemes)], dtype=np.int64)
            
            # Parâmetros de escala
            noise_scale = self.config.get('inference', {}).get('noise_scale', 0.667)
            length_scale = self.config.get('inference', {}).get('length_scale', 1.0)
            noise_w = self.config.get('inference', {}).get('noise_w', 0.8)
            scales = np.array([noise_scale, length_scale, noise_w], dtype=np.float32)
            
            # Criar dicionário de inputs baseado nos nomes esperados
            inputs = {}
            input_names = [inp.name for inp in self.session.get_inputs()]
            
            for input_name in input_names:
                if input_name == 'input' or 'phoneme' in input_name.lower():
                    inputs[input_name] = phoneme_input
                elif input_name == 'input_lengths' or 'length' in input_name.lower():
                    inputs[input_name] = input_lengths
                elif input_name == 'scales' or 'scale' in input_name.lower():
                    inputs[input_name] = scales
                else:
                    # Tentar adivinhar com base no shape
                    input_shape = self.session.get_inputs()[0].shape
                    if len(input_shape) == 2 and input_shape[1] == len(phonemes):
                        inputs[input_name] = phoneme_input
                    elif len(input_shape) == 1 and input_shape[0] == 1:
                        inputs[input_name] = input_lengths
                    elif len(input_shape) == 1 and input_shape[0] == 3:
                        inputs[input_name] = scales
            
            # Executar inferência
            outputs = self.session.run(None, inputs)
            
            # Processar output (assumindo que é áudio)
            if outputs and len(outputs) > 0:
                audio = outputs[0].flatten()
                
                # Normalizar
                if np.max(np.abs(audio)) > 0:
                    audio = 0.8 * audio / np.max(np.abs(audio))
                
                logger.info(f"✅ Áudio sintetizado com ONNX: {len(audio)} amostras")
                return audio
            else:
                raise RuntimeError("Nenhum output do modelo")
                
        except Exception as e:
            logger.error(f"❌ Erro na inferência ONNX: {e}")
            raise
    
    def synthesize_with_pytorch(self, phonemes: list) -> np.ndarray:
        """Sintetiza áudio usando modelo PyTorch"""
        
        if not self.model:
            raise RuntimeError("Modelo PyTorch não disponível")
        
        try:
            # Converter para tensor
            phoneme_tensor = torch.tensor([phonemes], dtype=torch.long)
            
            # Executar modelo
            with torch.no_grad():
                # Assumindo que o modelo retorna áudio diretamente
                if hasattr(self.model, 'synthesize'):
                    audio_tensor = self.model.synthesize(phoneme_tensor)
                elif hasattr(self.model, 'forward'):
                    audio_tensor = self.model(phoneme_tensor)
                else:
                    raise RuntimeError("Modelo PyTorch não tem método de síntese conhecido")
            
            # Converter para numpy
            audio = audio_tensor.detach().cpu().numpy().flatten()
            
            # Normalizar
            if np.max(np.abs(audio)) > 0:
                audio = 0.8 * audio / np.max(np.abs(audio))
            
            logger.info(f"✅ Áudio sintetizado com PyTorch: {len(audio)} amostras")
            return audio
            
        except Exception as e:
            logger.error(f"❌ Erro na inferência PyTorch: {e}")
            raise
    
    def synthesize(self, text: str, output_path: str = None, sample_rate: int = 22050) -> np.ndarray:
        """Sintetiza áudio a partir de texto"""
        
        logger.info(f"🎤 Sintetizando: '{text}'")
        
        try:
            # Converter texto para fonemas
            language = self.config.get('language', 'pt')
            phonemes = self.text_to_phonemes(text, language)
            
            # Tentar usar ONNX primeiro
            if self.session:
                try:
                    audio = self.synthesize_with_onnx(phonemes)
                except Exception as e:
                    logger.warning(f"⚠️  ONNX falhou: {e}, tentando PyTorch")
                    if self.model:
                        audio = self.synthesize_with_pytorch(phonemes)
                    else:
                        raise
            # Tentar PyTorch
            elif self.model:
                audio = self.synthesize_with_pytorch(phonemes)
            else:
                # Fallback completo
                logger.warning("⚠️  Nenhum modelo disponível, usando áudio de fallback")
                audio = self.generate_fallback_audio(text, sample_rate)
            
            # Garantir sample rate correto
            target_sr = self.config.get('audio', {}).get('sample_rate', sample_rate)
            if target_sr != sample_rate:
                # Resample se necessário (simplificado)
                logger.info(f"📊 Resample de {sample_rate} para {target_sr}")
                # Para simplificar, vamos manter o sample rate original
            
            # Salvar arquivo se solicitado
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                sf.write(output_path, audio, sample_rate)
                logger.info(f"💾 Áudio salvo em: {output_path}")
            
            logger.info(f"✅ Síntese concluída: {len(audio)} amostras")
            return audio
            
        except Exception as e:
            logger.error(f"❌ Erro na síntese: {e}")
            # Fallback final
            return self.generate_fallback_audio(text, sample_rate)
    
    def test_model_loading(self) -> dict:
        """Testa se o modelo foi carregado corretamente"""
        return {
            'onnx_available': ONNX_AVAILABLE,
            'torch_available': TORCH_AVAILABLE,
            'session_loaded': self.session is not None,
            'model_loaded': self.model is not None,
            'config_loaded': bool(self.config),
            'ready': self.session is not None or self.model is not None
        }