#!/usr/bin/env python3
"""Integração com Piper TTS usando CLI oficial via subprocess."""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PiperTTSInference:
    """Wrapper usando Piper CLI via subprocess."""

    def __init__(self, model_path: str, config_path: str):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self._config_data = {}

        # Carregar configuração JSON
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            logger.info("✅ Configuração Piper carregada com sucesso")
        except Exception as exc:
            logger.error(f"❌ Falha ao carregar configuração: {exc}")
            raise

        # Verificar se modelo existe
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {self.model_path}")

    @property
    def sample_rate(self) -> int:
        """Retorna sample rate do modelo."""
        return int(self._config_data.get('audio', {}).get('sample_rate', 22050))

    def synthesize(self, text: str, output_path: str | None = None) -> np.ndarray:
        """Sintetiza áudio usando Piper CLI via subprocess."""

        logger.info(f"🎤 Sintetizando com Piper CLI: '{text}'")

        # Criar arquivo temporário para o texto
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', suffix='.txt', delete=False
        ) as text_file:
            text_file.write(text)
            text_file_path = text_file.name

        # Criar arquivo temporário para o áudio (ou usar output_path)
        if output_path:
            wav_file_path = output_path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            wav_file = tempfile.NamedTemporaryFile(
                suffix='.wav', delete=False
            )
            wav_file.close()
            wav_file_path = wav_file.name

        try:
            # Executar Piper CLI
            cmd = [
                sys.executable,
                '-m',
                'piper',
                '--model',
                str(self.model_path),
                '--config',
                str(self.config_path),
                '--input-file',
                text_file_path,
                '--output-file',
                wav_file_path,
            ]

            logger.info(f"🚀 Executando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                logger.debug(f"Piper stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"Piper stderr: {result.stderr}")

            # Carregar áudio gerado
            audio, sr = sf.read(wav_file_path, dtype='float32')
            logger.info(f"✅ Síntese concluída: {len(audio)} amostras @ {sr}Hz")

            return audio

        except subprocess.CalledProcessError as exc:
            logger.error(f"❌ Erro ao executar Piper CLI: {exc}")
            logger.error(f"stdout: {exc.stdout}")
            logger.error(f"stderr: {exc.stderr}")
            raise RuntimeError(f"Piper CLI falhou: {exc.stderr}")

        except Exception as exc:
            logger.error(f"❌ Erro durante síntese: {exc}")
            raise

        finally:
            # Limpar arquivo temporário de texto
            try:
                os.unlink(text_file_path)
            except Exception:
                pass

            # Limpar arquivo temporário de áudio se não for output_path
            if not output_path:
                try:
                    os.unlink(wav_file_path)
                except Exception:
                    pass

    def test_model_loading(self) -> dict:
        """Retorna status básico do carregamento."""

        return {
            'ready': self.model_path.exists() and bool(self._config_data),
            'config_loaded': bool(self._config_data),
            'session_loaded': True,
            'model_loaded': self.model_path.exists(),
            'sample_rate': self.sample_rate,
            'language': self._config_data.get('espeak', {}).get('voice'),
        }