import json
import urllib.request
from collections import defaultdict

URL = "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json"
with urllib.request.urlopen(URL, timeout=60) as resp:
    catalog = json.load(resp)

languages = defaultdict(list)
for key, info in catalog.items():
    language = info.get("language") or {}
    code = (language.get("code") or "").lower()
    family = (language.get("family") or "").lower()
    quality = info.get("quality") or "unknown"
    name_native = language.get("name_native") or language.get("name_english") or ""
    languages[code].append((key, quality, name_native))
    if family and family != code:
        languages[family].append((key, quality, name_native))

for code in sorted(languages):
    if code in {"es", "fr", "it", "ru"} or code.startswith(("es-", "fr-", "it-", "ru-")):
        print(f"[{code}] {len(languages[code])} vozes")
        for key, quality, name in sorted(languages[code]):
            print(f"  {key:35s} | {quality:6s} | {name}")
