#!/usr/bin/env python3
"""
Sistema de Transcrição Automática para Geração de CSV - Piper TTS (Versão Robusta)
"""
import os
import json
import csv
import librosa
import soundfile as sf
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading
import time
import re

# Importações condicionais para diferentes engines de transcrição
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class AutoTranscriber:
    """Sistema de transcrição automática com múltiplos engines (versão robusta)"""
    
    def __init__(self, lazy_loading=True):
        self.engines = {
            'whisper': self._setup_whisper,
            'google': self._setup_google,
            'wav2vec2': self._setup_wav2vec2,
            'vosk': self._setup_vosk
        }
        
        self.available_engines = []
        self.current_engine = None
        self.engine_name = None
        self.transcription_status = {
            'is_running': False,
            'progress': 0,
            'current_file': '',
            'total_files': 0,
            'completed_files': 0,
            'errors': [],
            'results': []
        }
        
        # Se não for lazy loading, verifica engines disponíveis na inicialização
        if not lazy_loading:
            self._check_available_engines()
    
    def _check_available_engines(self):
        """Verifica quais engines estão disponíveis (com lazy loading)"""
        print("🔍 Verificando engines de transcrição disponíveis...")
        
        available = []
        
        # Whisper (OpenAI) - apenas verificar se está instalado
        if WHISPER_AVAILABLE:
            available.append('whisper')
            print("✅ Whisper (OpenAI) - Instalado")
        
        # Google Speech Recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            available.append('google')
            print("✅ Google Speech Recognition - Instalado")
        
        # Wav2Vec2 (Transformers) - apenas verificar se está instalado
        if TRANSFORMERS_AVAILABLE:
            available.append('wav2vec2')
            print("✅ Wav2Vec2 (Facebook) - Instalado")
        
        self.available_engines = available
        
        if not available:
            print("❌ Nenhum engine de transcrição disponível!")
            print("💡 Instale pelo menos um: pip install openai-whisper speechrecognition transformers")
        
        return available
    
    def _setup_whisper(self):
        """Configura Whisper (com lazy loading)"""
        if not WHISPER_AVAILABLE:
            return None
        
        try:
            # Carregar modelo (base é um bom compromisso entre velocidade e qualidade)
            print("🔄 Carregando modelo Whisper...")
            model = whisper.load_model("base")
            print("✅ Whisper carregado com sucesso")
            return model
        except Exception as e:
            print(f"❌ Erro ao carregar Whisper: {e}")
            return None
    
    def _setup_google(self):
        """Configura Google Speech Recognition"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            return None
        
        try:
            recognizer = sr.Recognizer()
            print("✅ Google Speech Recognition configurado")
            return recognizer
        except Exception as e:
            print(f"❌ Erro ao configurar Google: {e}")
            return None
    
    def _setup_wav2vec2(self):
        """Configura Wav2Vec2 (com lazy loading)"""
        if not TRANSFORMERS_AVAILABLE:
            return None
        
        try:
            print("🔄 Carregando modelo Wav2Vec2...")
            pipe = pipeline("automatic-speech-recognition", 
                          model="facebook/wav2vec2-base-960h")
            print("✅ Wav2Vec2 configurado")
            return pipe
        except Exception as e:
            print(f"❌ Erro ao configurar Wav2Vec2: {e}")
            return None
    
    def _setup_vosk(self):
        """Configura Vosk (offline)"""
        try:
            import vosk
            # Implementar configuração do Vosk se necessário
            return None
        except ImportError:
            return None
    
    def get_available_engines(self) -> List[str]:
        """Retorna lista de engines disponíveis (verifica se ainda não verificou)"""
        if not self.available_engines:
            self._check_available_engines()
        return self.available_engines.copy()
    
    def set_engine(self, engine_name: str) -> bool:
        """Define o engine de transcrição (com lazy loading)"""
        # Primeiro verificar se o engine está disponível
        available = self.get_available_engines()
        if engine_name not in available:
            print(f"❌ Engine '{engine_name}' não disponível")
            return False
        
        try:
            # Agora sim, carregar o modelo
            self.current_engine = self.engines[engine_name]()
            self.engine_name = engine_name
            print(f"✅ Engine '{engine_name}' ativado")
            return True
        except Exception as e:
            print(f"❌ Erro ao ativar engine '{engine_name}': {e}")
            return False
    
    def transcribe_audio(self, audio_path: str, language: str = "pt") -> Optional[str]:
        """Transcreve um único arquivo de áudio"""
        if not self.current_engine:
            print("❌ Nenhum engine de transcrição configurado")
            return None
        
        try:
            # Carregar e preprocessar áudio
            audio, sr_rate = librosa.load(audio_path, sr=16000)  # 16kHz para compatibilidade
            
            if self.engine_name == 'whisper':
                return self._transcribe_whisper(audio_path, language)
            elif self.engine_name == 'google':
                return self._transcribe_google(audio, sr_rate, language)
            elif self.engine_name == 'wav2vec2':
                return self._transcribe_wav2vec2(audio, sr_rate)
            
        except Exception as e:
            print(f"❌ Erro na transcrição de {audio_path}: {e}")
            return None
    
    def _transcribe_whisper(self, audio_path: str, language: str) -> Optional[str]:
        """Transcrição com Whisper"""
        try:
            result = self.current_engine.transcribe(audio_path, language=language)
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Erro Whisper: {e}")
            return None
    
    def _transcribe_google(self, audio: any, sr_rate: int, language: str) -> Optional[str]:
        """Transcrição com Google"""
        try:
            # Converter para formato compatível
            temp_path = "temp_audio.wav"
            sf.write(temp_path, audio, sr_rate)
            
            # Usar SpeechRecognition
            with sr.AudioFile(temp_path) as source:
                audio_data = self.current_engine.record(source)
            
            # Mapear códigos de idioma
            lang_map = {
                'pt': 'pt-BR',
                'en': 'en-US',
                'es': 'es-ES',
                'fr': 'fr-FR'
            }
            
            text = self.current_engine.recognize_google(
                audio_data, 
                language=lang_map.get(language, 'pt-BR')
            )
            
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return text.strip()
            
        except Exception as e:
            print(f"❌ Erro Google: {e}")
            return None
    
    def _transcribe_wav2vec2(self, audio: any, sr_rate: int) -> Optional[str]:
        """Transcrição com Wav2Vec2"""
        try:
            result = self.current_engine(audio)
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Erro Wav2Vec2: {e}")
            return None
    
    def batch_transcribe(self, audio_dir: str, output_csv: str, 
                        engine: str = "whisper", language: str = "pt",
                        callback=None) -> bool:
        """Transcrição em lote de uma pasta de áudios"""
        
        audio_path = Path(audio_dir)
        if not audio_path.exists():
            print(f"❌ Diretório não encontrado: {audio_dir}")
            return False
        
        # Encontrar arquivos de áudio
        audio_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg'}
        audio_files = [f for f in audio_path.iterdir() 
                      if f.suffix.lower() in audio_extensions]
        
        if not audio_files:
            print(f"❌ Nenhum arquivo de áudio encontrado em {audio_dir}")
            return False
        
        print(f"📁 Encontrados {len(audio_files)} arquivos de áudio")
        
        # Configurar engine
        if not self.set_engine(engine):
            return False
        
        # Inicializar status
        self.transcription_status = {
            'is_running': True,
            'progress': 0,
            'current_file': '',
            'total_files': len(audio_files),
            'completed_files': 0,
            'errors': [],
            'results': []
        }
        
        # Processar arquivos
        results = []
        for i, audio_file in enumerate(audio_files):
            try:
                self.transcription_status['current_file'] = str(audio_file)
                self.transcription_status['progress'] = (i / len(audio_files)) * 100
                
                print(f"🎵 Processando: {audio_file.name}")
                
                # Transcrever
                text = self.transcribe_audio(str(audio_file), language)
                
                if text:
                    # Limpar e formatar texto
                    text = self._clean_text(text)
                    results.append({
                        'id': audio_file.stem,
                        'text': text,
                        'file': str(audio_file)
                    })
                    print(f"✅ Transcrição: {text[:50]}...")
                else:
                    error_msg = f"Falha na transcrição de {audio_file.name}"
                    self.transcription_status['errors'].append(error_msg)
                    print(f"❌ {error_msg}")
                
                self.transcription_status['completed_files'] = i + 1
                
                # Callback opcional
                if callback:
                    callback(self.transcription_status)
                
            except Exception as e:
                error_msg = f"Erro em {audio_file.name}: {str(e)}"
                self.transcription_status['errors'].append(error_msg)
                print(f"❌ {error_msg}")
        
        # Salvar resultados
        self.transcription_status['results'] = results
        self.transcription_status['is_running'] = False
        self.transcription_status['progress'] = 100
        
        success = self._save_csv(results, output_csv)
        
        print(f"✅ Processamento concluído: {len(results)}/{len(audio_files)} arquivos")
        return success
    
    def _clean_text(self, text: str) -> str:
        """Limpa e formata o texto transcrito"""
        if not text:
            return ""
        
        # Remover espaços extras
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Capitalizar primeira letra
        if text:
            text = text[0].upper() + text[1:]
        
        # Adicionar ponto final se não houver pontuação
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def _save_csv(self, results: List[Dict], output_path: str) -> bool:
        """Salva resultados em arquivo CSV"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                for result in results:
                    # Formato: id|texto
                    csvfile.write(f"{result['id']}|{result['text']}\n")
            
            print(f"✅ CSV salvo: {output_path}")
            print(f"📊 Total de transcrições: {len(results)}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")
            return False
    
    def get_transcription_status(self) -> Dict:
        """Retorna status atual da transcrição"""
        return self.transcription_status.copy()

class CSVGenerator:
    """Gerador de CSV com múltiplas opções"""
    
    def __init__(self):
        self.transcriber = AutoTranscriber()
    
    def create_from_text_file(self, text_file: str, audio_dir: str, output_csv: str) -> bool:
        """Cria CSV a partir de arquivo de texto com uma linha por áudio"""
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Encontrar arquivos de áudio
            audio_path = Path(audio_dir)
            audio_files = sorted([f for f in audio_path.iterdir() 
                                if f.suffix.lower() in {'.wav', '.mp3', '.flac'}])
            
            if len(lines) != len(audio_files):
                print(f"⚠️  Aviso: {len(lines)} linhas de texto, {len(audio_files)} arquivos de áudio")
            
            # Criar CSV
            results = []
            for i, (audio_file, text) in enumerate(zip(audio_files, lines)):
                results.append({
                    'id': audio_file.stem,
                    'text': text,
                    'file': audio_file.name
                })
            
            return self._save_csv_results(results, output_csv)
            
        except Exception as e:
            print(f"❌ Erro ao criar CSV do arquivo de texto: {e}")
            return False
    
    def create_from_json(self, json_file: str, output_csv: str) -> bool:
        """Cria CSV a partir de arquivo JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = []
            for item in data:
                if 'id' in item and 'text' in item:
                    results.append({
                        'id': item['id'],
                        'text': item['text'],
                        'speaker': item.get('speaker', '')
                    })
            
            return self._save_csv_results(results, output_csv)
            
        except Exception as e:
            print(f"❌ Erro ao criar CSV do JSON: {e}")
            return False
    
    def create_interactive(self, audio_dir: str, output_csv: str) -> bool:
        """Cria CSV de forma interativa, reproduzindo áudios"""
        try:
            audio_path = Path(audio_dir)
            audio_files = sorted([f for f in audio_path.iterdir() 
                                if f.suffix.lower() in {'.wav', '.mp3', '.flac'}])
            
            if not audio_files:
                print("❌ Nenhum arquivo de áudio encontrado")
                return False
            
            print(f"🎵 Modo interativo: {len(audio_files)} arquivos")
            print("💡 Para cada áudio, digite a transcrição ou 'skip' para pular")
            
            results = []
            for i, audio_file in enumerate(audio_files):
                print(f"\n📁 Arquivo {i+1}/{len(audio_files)}: {audio_file.name}")
                
                # Aqui você poderia integrar um player de áudio
                # Por enquanto, apenas solicita a transcrição
                
                text = input("📝 Digite a transcrição: ").strip()
                
                if text.lower() == 'skip':
                    continue
                
                if text:
                    results.append({
                        'id': audio_file.stem,
                        'text': text,
                        'file': audio_file.name
                    })
            
            return self._save_csv_results(results, output_csv)
            
        except KeyboardInterrupt:
            print("\n⏹️  Processo interrompido pelo usuário")
            return False
        except Exception as e:
            print(f"❌ Erro no modo interativo: {e}")
            return False
    
    def _save_csv_results(self, results: List[Dict], output_path: str) -> bool:
        """Salva resultados em CSV"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                for result in results:
                    if 'speaker' in result and result['speaker']:
                        # Formato multi-speaker: id|speaker|text
                        csvfile.write(f"{result['id']}|{result['speaker']}|{result['text']}\n")
                    else:
                        # Formato single-speaker: id|text
                        csvfile.write(f"{result['id']}|{result['text']}\n")
            
            print(f"✅ CSV salvo: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")
            return False

# Instância global com lazy loading
global_transcriber = AutoTranscriber(lazy_loading=True)
global_csv_generator = CSVGenerator()

def get_transcription_engines() -> List[str]:
    """Retorna engines de transcrição disponíveis (lazy loading)"""
    return global_transcriber.get_available_engines()

def start_auto_transcription(audio_dir: str, output_csv: str, 
                           engine: str = "whisper", language: str = "pt",
                           callback=None) -> bool:
    """Inicia transcrição automática"""
    return global_transcriber.batch_transcribe(
        audio_dir, output_csv, engine, language, callback
    )

def get_transcription_status() -> Dict:
    """Retorna status da transcrição"""
    return global_transcriber.get_transcription_status()

if __name__ == "__main__":
    # Teste do sistema
    print("🧪 Testando sistema de transcrição automática...")
    
    transcriber = AutoTranscriber(lazy_loading=False)  # Forçar verificação
    print(f"📋 Engines disponíveis: {transcriber.get_available_engines()}")
    
    # Exemplo de uso
    if transcriber.available_engines:
        print("\n✅ Sistema pronto para uso!")
        print("\n📝 Exemplos de uso:")
        print("1. Transcrição automática: transcriber.batch_transcribe('audio/', 'metadata.csv')")
        print("2. CSV de arquivo texto: csv_gen.create_from_text_file('texts.txt', 'audio/', 'metadata.csv')")
        print("3. Modo interativo: csv_gen.create_interactive('audio/', 'metadata.csv')")
    else:
        print("\n❌ Instale pelo menos um engine:")
        print("pip install openai-whisper")
        print("pip install SpeechRecognition")
        print("pip install transformers torch")