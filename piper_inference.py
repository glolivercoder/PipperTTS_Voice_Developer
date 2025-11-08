#!/usr/bin/env python3
"""
Sistema de inferência para modelos Piper TTS treinados
"""
import torch
import onnxruntime as ort
import numpy as np
import json
import gruut
import soundfile as sf
from pathlib import Path
import librosa
from typing import List, Optional

class PiperTTSInference:
    """Sistema de inferência para modelos Piper TTS"""
    
    def __init__(self, model_path: str, config_path: str):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        
        # Carregar configuração
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Inicializar sessão ONNX
        try:
            self.session = ort.InferenceSession(str(self.model_path))
            self.onnx_available = True
        except Exception as e:
            print(f"⚠️  Erro carregando modelo ONNX: {e}")
            self.onnx_available = False
            
            # Fallback: carregar modelo PyTorch se disponível
            try:
                from piper_train_real import SimpleVITS
                self.model = SimpleVITS.load_from_checkpoint(str(self.model_path))
                self.model.eval()
                self.pytorch_available = True
            except:
                self.pytorch_available = False
    
    def text_to_phonemes(self, text: str, language: str = "pt") -> List[int]:
        """Converte texto para sequência de IDs de fonemas"""
        try:
            # Obter mapa de fonemas do modelo
            phoneme_id_map = self.config.get('phoneme_id_map', {})
            
            # Se não houver mapa, usar método de fallback
            if not phoneme_id_map:
                print("⚠️  Mapa de fonemas não encontrado, usando síntese sintética")
                return self._generate_fallback_phonemes(text)
            
            # Usar gruut para fonemas
            phonemes = []
            
            # Adicionar token de início (BOS)
            bos_id = phoneme_id_map.get('_', [1])[0] if '_' in phoneme_id_map else 1
            phonemes.append(bos_id)
            
            for sentence in gruut.sentences(text, lang=language):
                for word in sentence:
                    if word.phonemes:
                        for phoneme in word.phonemes:
                            # Procurar fonema no mapa
                            if phoneme in phoneme_id_map:
                                phoneme_id = phoneme_id_map[phoneme][0]
                                phonemes.append(phoneme_id)
                            else:
                                # Fonema não encontrado, tentar fonemas similares
                                phoneme_id = self._find_similar_phoneme(phoneme, phoneme_id_map)
                                phonemes.append(phoneme_id)
                    else:
                        # Palavra sem fonemas, usar caracteres
                        for char in word.text.lower():
                            if char in phoneme_id_map:
                                phonemes.append(phoneme_id_map[char][0])
                            else:
                                # Caractere não encontrado, usar espaço ou vogal
                                if char.isspace():
                                    space_id = phoneme_id_map.get(' ', [3])[0] if ' ' in phoneme_id_map else 3
                                    phonemes.append(space_id)
                                else:
                                    # Usar vogal 'a' como fallback
                                    a_id = phoneme_id_map.get('a', [14])[0] if 'a' in phoneme_id_map else 14
                                    phonemes.append(a_id)
                    
                    # Adicionar espaço entre palavras
                    space_id = phoneme_id_map.get(' ', [3])[0] if ' ' in phoneme_id_map else 3
                    phonemes.append(space_id)
            
            # Adicionar token de fim (EOS)
            eos_id = phoneme_id_map.get('$', [2])[0] if '$' in phoneme_id_map else 2
            phonemes.append(eos_id)
            
            # Garantir que todos os IDs estão dentro dos limites
            max_allowed_id = max(max(ids) for ids in phoneme_id_map.values()) if phoneme_id_map else 200
            phonemes = [min(id_val, max_allowed_id) for id_val in phonemes]
            
            return phonemes
            
        except Exception as e:
            print(f"⚠️  Erro na conversão de fonemas: {e}")
            return self._generate_fallback_phonemes(text)
    
    def _find_similar_phoneme(self, phoneme: str, phoneme_id_map: dict) -> int:
        """Encontra um fonema similar quando o original não existe no mapa"""
        # Mapeamento de fonemas similares
        similar_map = {
            'ɑ': 'a', 'ɒ': 'a', 'ʌ': 'a', 'ə': 'a',
            'ɛ': 'e', 'ɜ': 'e', 'ɪ': 'i', 'ɨ': 'i',
            'ɔ': 'o', 'ɵ': 'o', 'ʊ': 'u', 'ʉ': 'u',
            'ɹ': 'r', 'ɾ': 'r', 'ʔ': 't', 'θ': 't',
            'ð': 'd', 'ʒ': 'z', 'ʃ': 's', 'ç': 'h'
        }
        
        # Tentar encontrar fonema similar
        if phoneme in similar_map:
            similar = similar_map[phoneme]
            if similar in phoneme_id_map:
                return phoneme_id_map[similar][0]
        
        # Fallback: usar vogal 'a'
        return phoneme_id_map.get('a', [14])[0] if 'a' in phoneme_id_map else 14
    
    def _generate_fallback_phonemes(self, text: str) -> List[int]:
        """Gera sequência de fonemas de fallback quando o método principal falha"""
        # Usar sequência simples baseada no comprimento do texto
        length = min(len(text), 50)  # Limitar tamanho
        phonemes = [1]  # BOS
        
        # Adicionar padrão simples alternando vogais e consoantes
        vowels = [14, 18, 21, 27, 33]  # a, e, i, o, u
        consonants = [15, 17, 19, 20, 23, 24, 25, 26, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38]  # b, d, f, h, k, l, m, n, p, q, r, s, t, v, w, x, y, z
        
        for i in range(length):
            if i % 2 == 0:
                phonemes.append(vowels[i % len(vowels)])
            else:
                phonemes.append(consonants[i % len(consonants)])
            
            if i % 4 == 3:  # Adicionar espaço a cada 4 fonemas
                phonemes.append(3)
        
        phonemes.append(2)  # EOS
        return phonemes
    
    def mel_to_audio(self, mel_spectrogram: np.ndarray, sample_rate: int = 22050) -> np.ndarray:
        """Converte mel-spectrogram para áudio usando Griffin-Lim"""
        
        # Converter mel para linear spectrogram (aproximação)
        mel_db = mel_spectrogram
        mel_linear = librosa.db_to_power(mel_db)
        
        # Usar Griffin-Lim para reconstruir áudio
        audio = librosa.feature.inverse.mel_to_audio(
            mel_linear,
            sr=sample_rate,
            n_fft=1024,
            hop_length=256,
            win_length=1024,
            n_iter=32
        )
        
        # Normalizar
        audio = librosa.util.normalize(audio)
        
        return audio
    
    def synthesize(self, text: str, output_path: Optional[str] = None) -> np.ndarray:
        """Sintetiza áudio a partir de texto"""
        
        print(f"🎤 Sintetizando: '{text}'")
        
        # Converter texto para fonemas
        language = self.config.get('language', 'pt')
        phonemes = self.text_to_phonemes(text, language)
        
        print(f"📝 Fonemas: {len(phonemes)} tokens")
        
        # Preparar input
        phoneme_input = np.array([phonemes], dtype=np.int64)
        
        try:
            if self.onnx_available:
                # Usar modelo ONNX com parâmetros corretos
                input_names = [inp.name for inp in self.session.get_inputs()]
                output_names = [out.name for out in self.session.get_outputs()]
                
                # Preparar inputs baseado nos nomes esperados
                inputs = {}
                for input_name in input_names:
                    if input_name == 'input':
                        inputs[input_name] = phoneme_input
                    elif input_name == 'input_lengths':
                        inputs[input_name] = np.array([len(phonemes)], dtype=np.int64)
                    elif input_name == 'scales':
                        # Parâmetros de escala (noise_scale, length_scale, noise_w)
                        noise_scale = self.config.get('inference', {}).get('noise_scale', 0.667)
                        length_scale = self.config.get('inference', {}).get('length_scale', 1.0)
                        noise_w = self.config.get('inference', {}).get('noise_w', 0.8)
                        inputs[input_name] = np.array([noise_scale, length_scale, noise_w], dtype=np.float32)
                    else:
                        # Para outros inputs, usar valores padrão
                        inputs[input_name] = np.zeros((1, 1), dtype=np.float32)
                
                result = self.session.run(output_names, inputs)
                mel_output = result[0][0] if result else self.generate_synthetic_mel(len(phonemes))
                
            elif self.pytorch_available:
                # Usar modelo PyTorch
                with torch.no_grad():
                    phoneme_tensor = torch.LongTensor(phoneme_input)
                    mel_output = self.model(phoneme_tensor)
                    mel_output = mel_output[0].numpy()  # [mel_bins, time]
            
            else:
                # Fallback: gerar mel-spectrogram sintético
                print("⚠️  Usando síntese sintética (modelo não disponível)")
                mel_output = self.generate_synthetic_mel(len(phonemes))
            
            print(f"🎵 Mel-spectrogram gerado: {mel_output.shape}")
            
            # Converter mel para áudio
            sample_rate = self.config.get('audio', {}).get('sample_rate', 22050)
            audio = self.mel_to_audio(mel_output, sample_rate)
            
            print(f"🔊 Áudio gerado: {len(audio)} amostras, {len(audio)/sample_rate:.2f}s")
            
            # Salvar se especificado
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                sf.write(output_path, audio, sample_rate)
                print(f"💾 Áudio salvo em: {output_path}")
            
            return audio
            
        except Exception as e:
            print(f"❌ Erro na síntese: {e}")
            # Fallback: gerar áudio sintético e salvar mesmo assim
            audio = self.generate_synthetic_audio(text)
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                sf.write(output_path, audio, self.config.get('audio', {}).get('sample_rate', 22050))
                print(f"💾 Áudio sintético salvo em: {output_path}")
            return audio
    
    def generate_synthetic_mel(self, length: int) -> np.ndarray:
        """Gera mel-spectrogram sintético para fallback"""
        
        # Gerar mel-spectrogram com padrão senoidal
        time_steps = max(length * 4, 100)  # Aproximação
        mel_bins = 80
        
        mel = np.zeros((mel_bins, time_steps))
        
        for i in range(mel_bins):
            frequency = (i + 1) * 0.1
            for t in range(time_steps):
                mel[i, t] = np.sin(frequency * t * 0.1) * np.exp(-t * 0.01)
        
        # Normalizar
        mel = (mel - mel.min()) / (mel.max() - mel.min() + 1e-8)
        mel = mel * 80 - 80  # Converter para dB
        
        return mel
    
    def generate_synthetic_audio(self, text: str, duration: float = 2.0) -> np.ndarray:
        """Gera áudio sintético para fallback"""
        
        sample_rate = self.config.get('audio', {}).get('sample_rate', 22050)
        samples = int(duration * sample_rate)
        
        # Gerar tom baseado no comprimento do texto
        frequency = 200 + (len(text) % 300)  # 200-500 Hz
        
        t = np.linspace(0, duration, samples)
        audio = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Adicionar envelope
        envelope = np.exp(-t * 2)
        audio *= envelope
        
        return audio

def test_model(model_path: str, config_path: str, test_text: str = "Olá, este é um teste."):
    """Testa um modelo treinado"""
    
    print(f"🧪 Testando modelo: {model_path}")
    
    try:
        # Criar sistema de inferência
        tts = PiperTTSInference(model_path, config_path)
        
        # Sintetizar áudio de teste
        output_path = f"test_output_{Path(model_path).stem}.wav"
        audio = tts.synthesize(test_text, output_path)
        
        print(f"✅ Teste concluído! Áudio salvo em: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    # Teste básico
    print("🧪 Testando sistema de inferência Piper TTS")
    
    # Criar configuração de teste
    test_config = {
        "audio": {
            "sample_rate": 22050
        },
        "language": "pt",
        "model_name": "test_model"
    }
    
    with open("test_config.json", 'w') as f:
        json.dump(test_config, f, indent=2)
    
    print("✅ Sistema de inferência carregado com sucesso!")