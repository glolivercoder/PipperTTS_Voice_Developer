# 🎤 Piper TTS - Interface de Treinamento de Vozes Clonadas

Uma interface web completa para treinar vozes personalizadas usando o Piper TTS, permitindo criar modelos de síntese de voz com sua própria voz ou qualquer voz desejada.

## 🚀 Instalação Rápida

### 1. Configuração Automática
```bash
# Clone o repositório (se ainda não fez)
git clone https://github.com/glolivercoder/PipperTTS_Voice_Developer.git
cd piper

# Execute o script de configuração
python setup_piper_training.py
```

### 2. Ativação do Ambiente
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Iniciar Interface
```bash
python web_interface.py
```

Acesse: **http://localhost:5000**

## 📋 Requisitos do Sistema

### Mínimos:
- Python 3.7+
- 8GB RAM
- 10GB espaço livre
- Placa de som

### Recomendados:
- Python 3.9+
- 16GB RAM
- GPU NVIDIA (para treinamento mais rápido)
- 50GB espaço livre

### Dependências do Sistema:
- **Linux:** `python3-dev`, `espeak-ng`, `build-essential`
- **macOS:** `espeak-ng` (via Homebrew)
- **Windows:** Visual Studio Build Tools

## 🎯 Como Usar

### Passo 1: Preparar Dados de Áudio

#### Requisitos de Áudio:
- **Formato:** WAV (recomendado), MP3, FLAC
- **Qualidade:** 22kHz, mono
- **Duração:** Mínimo 30 minutos, recomendado 1-2 horas
- **Ambiente:** Silencioso, sem eco
- **Microfone:** Boa qualidade, consistente

#### Dicas de Gravação:
- Mantenha distância consistente do microfone
- Fale com tom natural e velocidade normal
- Evite respiração audível
- Pause entre frases
- Use textos variados (notícias, literatura, conversação)

### Passo 2: Criar Arquivo Metadata

Crie um arquivo `metadata.csv` com o formato:
```csv
id|texto
```

**Exemplo:**
```csv
audio001|Olá, este é um exemplo de texto para treinamento.
audio002|A qualidade do áudio é muito importante para bons resultados.
audio003|Recomenda-se pelo menos trinta minutos de áudio limpo.
```

Para múltiplos falantes:
```csv
id|speaker|texto
audio001|pessoa1|Primeira pessoa falando este texto.
audio002|pessoa2|Segunda pessoa com voz diferente.
```

### Passo 3: Upload na Interface

1. Acesse a aba **"Upload de Dados"**
2. Digite o nome do modelo
3. Selecione os arquivos de áudio
4. Faça upload do metadata.csv
5. Clique em **"Enviar Arquivos"**

### Passo 4: Configurar Treinamento

1. Vá para a aba **"Treinamento"**
2. Selecione o modelo uploadado
3. Configure os parâmetros:
   - **Idioma:** pt-br (Português Brasil)
   - **Qualidade:** Medium (balanceado)
   - **Taxa de Amostragem:** 22050 Hz
   - **Falante único:** Marque se for uma só voz

### Passo 5: Iniciar Treinamento

1. Clique em **"Iniciar Treinamento"**
2. Monitore o progresso na interface
3. O processo pode levar de 30 minutos a várias horas
4. Acompanhe o log para verificar se está tudo correndo bem

### Passo 6: Testar o Modelo

1. Após o treinamento, vá para **"Modelos"**
2. Verifique se o modelo aparece como completo
3. Na aba **"Teste de Voz"**:
   - Selecione o modelo treinado
   - Digite um texto de teste
   - Clique em **"Gerar Áudio"**
   - Ouça o resultado

## ⚙️ Configurações Avançadas

### Qualidades de Modelo:
- **Baixa (16kHz):** Mais rápido, menor qualidade
- **Média (22kHz):** Balanceado, recomendado
- **Alta (22kHz):** Melhor qualidade, mais lento

### Parâmetros de Treinamento:
- **Épocas:** Número de ciclos de treinamento
- **Batch Size:** Quantidade de dados processados por vez
- **Learning Rate:** Velocidade de aprendizado

### Fine-tuning:
Para melhorar um modelo existente, você pode usar checkpoints pré-treinados disponíveis em:
https://huggingface.co/datasets/rhasspy/piper-checkpoints

## 🔧 Solução de Problemas

### Erro de Memória:
- Reduza o batch size
- Use qualidade "baixa"
- Feche outros programas

### Áudio com Ruído:
- Use software de limpeza de áudio (Audacity)
- Grave em ambiente mais silencioso
- Verifique configurações do microfone

### Treinamento Lento:
- Use GPU se disponível
- Reduza duração dos áudios
- Use qualidade "baixa" para testes

### Modelo não Funciona:
- Verifique se tem dados suficientes
- Confirme formato do metadata.csv
- Teste com textos similares aos de treinamento

## 📁 Estrutura de Arquivos

```
piper/
├── web_interface.py          # Interface web principal
├── setup_piper_training.py   # Script de configuração
├── install_dependencies.py   # Instalador de dependências
├── templates/
│   └── index.html           # Interface HTML
├── static/
│   ├── css/style.css        # Estilos
│   ├── js/script.js         # JavaScript
│   └── audio/               # Áudios gerados
├── uploads/                 # Arquivos enviados
├── training_data/           # Dados de treinamento
├── trained_models/          # Modelos finalizados
└── examples/                # Arquivos de exemplo
```

## 🎵 Formatos de Saída

### Arquivos Gerados:
- **modelo.onnx:** Modelo neural otimizado
- **modelo.onnx.json:** Configurações do modelo
- **checkpoints/:** Pontos de salvamento durante treinamento

### Uso dos Modelos:
```bash
# Via linha de comando
echo "Texto para falar" | piper -m modelo.onnx --output_file saida.wav

# Via Python
import piper
model = piper.PiperVoice.load("modelo.onnx")
audio = model.synthesize("Texto para falar")
```

## 🤝 Contribuição

Para contribuir com melhorias:

1. Fork o repositório
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Abra um Pull Request

## 📚 Recursos Adicionais

- [Documentação Oficial Piper](https://github.com/rhasspy/piper)
- [Guia de Treinamento Original](TRAINING.md)
- [Modelos Pré-treinados](https://huggingface.co/rhasspy)
- [Comunidade Rhasspy](https://community.rhasspy.org/)

## 📄 Licença

Este projeto segue a licença MIT do Piper TTS original.

## 🆘 Suporte

Para problemas específicos:
1. Verifique os logs na interface
2. Consulte a seção de solução de problemas
3. Abra uma issue no GitHub
4. Participe da comunidade Rhasspy

---

**Desenvolvido com ❤️ para a comunidade de síntese de voz**