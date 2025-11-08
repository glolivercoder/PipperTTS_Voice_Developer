# Migração para OHF-Voice/piper1-gpl

## 📋 Resumo

Este projeto foi migrado do repositório `rhasspy/piper` para `OHF-Voice/piper1-gpl`, que é o novo repositório oficial de desenvolvimento do Piper TTS.

## 🔄 Arquivos Modificados

Os seguintes arquivos foram atualizados para refletir o novo repositório:

1. **src/python_run/setup.py** - URL do repositório atualizada
2. **templates/Upload_Kaggle.html** - URL de clone atualizada

## 📦 Backup Criado

Um backup dos arquivos importantes foi criado no diretório `backup_importantes/` contendo:

- `web_interface.py` - Interface web principal
- `trained_models/` - Modelos treinados
- `static/` - Arquivos estáticos (CSS, JS, áudios)
- `templates/` - Templates HTML
- `README.md` - Documentação original
- `requirements.txt` - Dependências originais

## 🚀 Instalação da Nova Versão

### Opção 1: Script Automático

Execute o script de migração:

```bash
python install_ohf_voice.py
```

### Opção 2: Manual

1. Clone o novo repositório:
```bash
git clone https://github.com/OHF-Voice/piper1-gpl.git
```

2. Instale as dependências:
```bash
cd piper1-gpl
pip install -e .
```

## ⚠️ Notas Importantes

- O desenvolvimento do Piper TTS foi movido para `OHF-Voice/piper1-gpl`
- A versão antiga em `rhasspy/piper` não receberá mais atualizações
- Os modelos existentes devem continuar funcionando com a nova versão
- A API e interface web foram mantidas compatíveis

## 📚 Recursos

- [Repositório Oficial](https://github.com/OHF-Voice/piper1-gpl)
- [Documentação Original](README.md)
- [Modelos de Voz](VOICES.md)

## 🆘 Suporte

Se encontrar problemas durante a migração:

1. Verifique o backup em `backup_importantes/`
2. Consulte a documentação do novo repositório
3. Abra uma issue no repositório oficial