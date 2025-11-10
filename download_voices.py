#!/usr/bin/env python3
"""Ferramenta para baixar vozes oficiais do Piper TTS.

Este script consulta o catálogo `voices.json` hospedado no
repositório oficial (`rhasspy/piper-voices`) e baixa os arquivos
`.onnx` e `.onnx.json` correspondentes a cada voz.

⚠️ Atenção: baixar todas as vozes consome dezenas de gigabytes.
Use os filtros disponíveis (`--language`, `--quality`, `--search`)
para limitar o download conforme necessário.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator

import requests

VOICES_JSON_URL = "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json"
HF_BASE_RESOLVE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

logger = logging.getLogger("download_voices")


@dataclass
class Voice:
    """Metadados de uma voz disponível para download."""

    key: str
    language_code: str
    language_family: str | None
    quality: str
    files: Dict[str, Dict[str, str]]

    @property
    def short_slug(self) -> str:
        """Slug utilizado para nomear diretórios/arquivos locais."""

        return self.key.replace("/", "-")


def fetch_catalog() -> Dict[str, Voice]:
    """Carrega o catálogo oficial de vozes."""

    logger.info("🔄 Baixando catálogo de vozes: %s", VOICES_JSON_URL)
    response = requests.get(VOICES_JSON_URL, timeout=60)
    response.raise_for_status()

    raw_catalog = response.json()
    catalog: Dict[str, Voice] = {}

    for key, info in raw_catalog.items():
        language = info.get("language", {}) or {}
        catalog[key] = Voice(
            key=key,
            language_code=str(language.get("code", "")).lower(),
            language_family=str(language.get("family")) if language.get("family") else None,
            quality=str(info.get("quality", "unknown")),
            files=info.get("files", {}),
        )

    logger.info("📚 Catálogo carregado: %s vozes", len(catalog))
    return catalog


def should_include(voice: Voice, args: argparse.Namespace) -> bool:
    """Aplica filtros de linguagem/qualidade/pesquisa."""

    if args.languages:
        candidates = {voice.language_code, voice.language_code.split("-")[0]}
        if candidates.isdisjoint({lang.lower() for lang in args.languages}):
            return False

    if args.only_portuguese:
        if not voice.language_code.startswith("pt"):
            return False

    if args.qualities and voice.quality not in args.qualities:
        return False

    if args.search:
        keyword = args.search.lower()
        if keyword not in voice.key.lower():
            return False

    return True


def iter_voice_files(voice: Voice) -> Iterator[tuple[str, Path, Dict[str, str]]]:
    """Gera tuplas (url_relativa, caminho_destino, metadados)."""

    dest_dir = Path("trained_models") / voice.short_slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    for rel_path, metadata in voice.files.items():
        if not (rel_path.endswith(".onnx") or rel_path.endswith(".onnx.json")):
            continue

        suffix = ".onnx" if rel_path.endswith(".onnx") else ".onnx.json"
        dest_file = dest_dir / f"{voice.short_slug}{suffix}"
        yield rel_path, dest_file, metadata


def file_matches_md5(path: Path, expected_md5: str | None) -> bool:
    """Verifica se arquivo existente corresponde ao hash esperado."""

    if not expected_md5 or not path.exists():
        return False

    md5 = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(chunk)

    match = md5.hexdigest() == expected_md5
    if match:
        logger.debug("👍 Hash MD5 coincide para %s", path)
    else:
        logger.warning("⚠️ Hash MD5 divergente: %s (esperado %s)", path, expected_md5)
    return match


def download_file(url: str, destination: Path) -> None:
    """Efetua download via streaming."""

    logger.info("⬇️  %s", url)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    handle.write(chunk)


def download_voice(voice: Voice, args: argparse.Namespace) -> bool:
    """Baixa arquivos necessários de uma voz."""

    logger.info("\n📥 Voz: %s (%s | %s)", voice.key, voice.language_code, voice.quality)
    success = True

    for rel_path, dest_file, meta in iter_voice_files(voice):
        url = HF_BASE_RESOLVE + rel_path
        expected_md5 = meta.get("md5_digest") if isinstance(meta, dict) else None

        if dest_file.exists():
            if args.skip_existing:
                logger.info("⏭️  Ignorando existente: %s", dest_file)
                continue
            if file_matches_md5(dest_file, expected_md5):
                logger.info("✅ Já baixado: %s", dest_file)
                continue

        try:
            download_file(url, dest_file)
            if expected_md5 and not file_matches_md5(dest_file, expected_md5):
                raise ValueError("hash MD5 não confere")
            logger.info("✅ Arquivo salvo em %s", dest_file)
        except Exception as exc:  # pragma: no cover - download externo
            logger.error("❌ Falha ao baixar %s: %s", url, exc)
            success = False
            if dest_file.exists():
                dest_file.unlink(missing_ok=True)

    return success


def download_catalog(args: argparse.Namespace) -> list[Voice]:
    """Baixa vozes conforme filtros configured."""

    catalog = fetch_catalog()
    selected = [voice for voice in catalog.values() if should_include(voice, args)]

    if not selected:
        logger.warning("Nenhuma voz corresponde aos filtros informados.")
        return []

    logger.info("🎯 %s vozes selecionadas para download", len(selected))

    downloaded: list[Voice] = []
    for voice in selected:
        if download_voice(voice, args):
            downloaded.append(voice)

    return downloaded


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Baixa vozes oficiais do Piper TTS")
    parser.add_argument(
        "--languages",
        nargs="+",
        help="Filtra por códigos de idioma (ex: pt, pt-br, en, es).",
    )
    parser.add_argument(
        "--qualities",
        nargs="+",
        choices=["x_low", "low", "medium", "high"],
        help="Restringe por qualidade do modelo (quando disponível).",
    )
    parser.add_argument(
        "--search",
        help="Filtro textual aplicado à chave da voz (ex: 'amy', 'faber').",
    )
    parser.add_argument(
        "--only-portuguese",
        action="store_true",
        help="Baixa apenas vozes cujo código de idioma começa com 'pt'.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Não sobrescreve arquivos já presentes com hash válido.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Nível de log (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    try:
        downloaded = download_catalog(args)
    except requests.RequestException as exc:
        logger.error("Falha ao acessar catálogo de vozes: %s", exc)
        return 1

    if downloaded:
        logger.info("\n✅ %s vozes baixadas com sucesso.", len(downloaded))
        for voice in downloaded:
            logger.info("   • %s (%s | %s)", voice.key, voice.language_code, voice.quality)
        logger.info("\n📁 Diretório base: %s", Path("trained_models").resolve())
        return 0

    logger.warning("Nenhuma voz foi baixada.")
    return 2


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())