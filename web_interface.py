#!/usr/bin/env python3
"""
Interface Web para Treinamento de Vozes Clonadas - Piper TTS
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import os
import json
import subprocess
import threading
import time
from pathlib import Path
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configurações
UPLOAD_FOLDER = 'uploads'
TRAINING_FOLDER = 'training_data'
MODELS_FOLDER = 'trained_models'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'csv', 'txt'}

# Criar diretórios necessários
for folder in [UPLOAD_FOLDER, TRAINING_FOLDER, MODELS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Estado global do treinamento
training_status = {
    'is_training': False,
    'current_step': '',
    'progress': 0,
    'log': [],
    'model_name': ''
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'audio_files' not in request.files and 'metadata_file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        model_name = request.form.get('model_name', 'novo_modelo')
        model_dir = os.path.join(TRAINING_FOLDER, secure_filename(model_name))
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(os.path.join(model_dir, 'wav'), exist_ok=True)
        
        # Upload de arquivos de áudio
        audio_files = request.files.getlist('audio_files')
        uploaded_audio = []
        
        for file in audio_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(model_dir, 'wav', filename)
                file.save(filepath)
                uploaded_audio.append(filename)
        
        # Upload do arquivo metadata
        metadata_file = request.files.get('metadata_file')
        if metadata_file and allowed_file(metadata_file.filename):
            metadata_path = os.path.join(model_dir, 'metadata.csv')
            metadata_file.save(metadata_path)
        
        return jsonify({
            'success': True,
            'message': f'Arquivos enviados com sucesso para o modelo {model_name}',
            'audio_files': uploaded_audio,
            'model_dir': model_dir
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_training', methods=['POST'])
def start_training():
    global training_status
    
    if training_status['is_training']:
        return jsonify({'error': 'Já existe um treinamento em andamento'}), 400
    
    try:
        data = request.json
        model_name = data.get('model_name')
        language = data.get('language', 'pt-br')
        quality = data.get('quality', 'medium')
        sample_rate = data.get('sample_rate', 22050)
        single_speaker = data.get('single_speaker', True)
        
        model_dir = os.path.join(TRAINING_FOLDER, model_name)
        
        if not os.path.exists(model_dir):
            return jsonify({'error': 'Diretório do modelo não encontrado'}), 400
        
        # Iniciar treinamento em thread separada
        training_thread = threading.Thread(
            target=run_training_pipeline,
            args=(model_name, model_dir, language, quality, sample_rate, single_speaker)
        )
        training_thread.start()
        
        return jsonify({'success': True, 'message': 'Treinamento iniciado'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/training_status')
def get_training_status():
    return jsonify(training_status)

@app.route('/models')
def list_models():
    models = []
    if os.path.exists(MODELS_FOLDER):
        for item in os.listdir(MODELS_FOLDER):
            model_path = os.path.join(MODELS_FOLDER, item)
            if os.path.isdir(model_path):
                onnx_file = os.path.join(model_path, f"{item}.onnx")
                json_file = os.path.join(model_path, f"{item}.onnx.json")
                
                models.append({
                    'name': item,
                    'has_onnx': os.path.exists(onnx_file),
                    'has_json': os.path.exists(json_file),
                    'path': model_path
                })
    
    return jsonify(models)

@app.route('/training_datasets')
def list_training_datasets():
    """Lista datasets disponíveis para exportação"""
    datasets = []
    if os.path.exists(TRAINING_FOLDER):
        for item in os.listdir(TRAINING_FOLDER):
            dataset_path = os.path.join(TRAINING_FOLDER, item)
            if os.path.isdir(dataset_path):
                metadata_file = os.path.join(dataset_path, 'metadata.csv')
                wav_dir = os.path.join(dataset_path, 'wav')
                
                audio_count = 0
                if os.path.exists(wav_dir):
                    audio_files = [f for f in os.listdir(wav_dir) 
                                 if f.endswith(('.wav', '.mp3', '.flac'))]
                    audio_count = len(audio_files)
                
                datasets.append({
                    'name': item,
                    'has_metadata': os.path.exists(metadata_file),
                    'audio_count': audio_count,
                    'path': dataset_path,
                    'size_mb': get_folder_size(dataset_path)
                })
    
    return jsonify(datasets)

@app.route('/export_cloud', methods=['POST'])
def export_to_cloud():
    """Exporta dataset para treinamento em nuvem"""
    try:
        data = request.json
        dataset_name = data.get('dataset_name')
        platform = data.get('platform', 'colab')
        
        if not dataset_name:
            return jsonify({'error': 'Nome do dataset é obrigatório'}), 400
        
        dataset_path = os.path.join(TRAINING_FOLDER, dataset_name)
        if not os.path.exists(dataset_path):
            return jsonify({'error': 'Dataset não encontrado'}), 400
        
        # Iniciar exportação em thread separada
        export_thread = threading.Thread(
            target=run_cloud_export,
            args=(dataset_name, dataset_path, platform)
        )
        export_thread.start()
        
        return jsonify({'success': True, 'message': 'Exportação iniciada'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cloud_status')
def get_cloud_training_status():
    """Retorna status da exportação/treinamento em nuvem"""
    import cloud_training
    return jsonify(cloud_training.get_cloud_status())

@app.route('/download_package/<package_name>')
def download_package(package_name):
    """Download do pacote de treinamento"""
    try:
        package_path = os.path.join('cloud_exports', f"{package_name}")
        if os.path.exists(package_path):
            return send_file(package_path, as_attachment=True)
        else:
            return jsonify({'error': 'Pacote não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_remote_monitoring', methods=['POST'])
def start_remote_monitoring():
    """Inicia monitoramento remoto de treinamento"""
    try:
        data = request.json
        session_config = {
            'platform': data.get('platform', 'colab'),
            'session_id': data.get('session_id'),
            'notebook_url': data.get('notebook_url'),
            'model_name': data.get('model_name'),
            'start_time': time.time()
        }
        
        import remote_monitor
        success = remote_monitor.start_remote_monitoring(session_config)
        
        if success:
            return jsonify({'success': True, 'message': 'Monitoramento iniciado'})
        else:
            return jsonify({'error': 'Falha ao iniciar monitoramento'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop_remote_monitoring', methods=['POST'])
def stop_remote_monitoring():
    """Para monitoramento remoto"""
    try:
        import remote_monitor
        remote_monitor.stop_remote_monitoring()
        return jsonify({'success': True, 'message': 'Monitoramento parado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remote_status')
def get_remote_status():
    """Retorna status do monitoramento remoto"""
    try:
        import remote_monitor
        status = remote_monitor.get_monitoring_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_trained_model', methods=['POST'])
def download_trained_model():
    """Baixa modelo treinado da nuvem"""
    try:
        data = request.json
        model_url = data.get('model_url')
        model_name = data.get('model_name')
        
        if not model_url or not model_name:
            return jsonify({'error': 'URL e nome do modelo são obrigatórios'}), 400
        
        # Baixar modelo em thread separada
        download_thread = threading.Thread(
            target=download_model_from_cloud,
            args=(model_url, model_name)
        )
        download_thread.start()
        
        return jsonify({'success': True, 'message': 'Download iniciado'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcription_engines')
def get_transcription_engines():
    """Retorna engines de transcrição disponíveis"""
    try:
        import auto_transcription
        engines = auto_transcription.get_transcription_engines()
        return jsonify({
            'engines': engines,
            'default': 'whisper' if 'whisper' in engines else engines[0] if engines else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/start_transcription', methods=['POST'])
def start_auto_transcription():
    """Inicia transcrição automática de áudios"""
    try:
        data = request.json
        model_name = data.get('model_name')
        engine = data.get('engine', 'whisper')
        language = data.get('language', 'pt')
        
        if not model_name:
            return jsonify({'error': 'Nome do modelo é obrigatório'}), 400
        
        audio_dir = os.path.join(TRAINING_FOLDER, model_name, 'wav')
        output_csv = os.path.join(TRAINING_FOLDER, model_name, 'metadata.csv')
        
        if not os.path.exists(audio_dir):
            return jsonify({'error': 'Diretório de áudio não encontrado'}), 400
        
        # Iniciar transcrição em thread separada
        transcription_thread = threading.Thread(
            target=run_auto_transcription,
            args=(audio_dir, output_csv, engine, language)
        )
        transcription_thread.start()
        
        return jsonify({'success': True, 'message': 'Transcrição automática iniciada'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/transcription_status')
def get_transcription_status():
    """Retorna status da transcrição automática"""
    try:
        import auto_transcription
        status = auto_transcription.get_transcription_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_text_file', methods=['POST'])
def upload_text_file():
    """Upload de arquivo de texto para gerar CSV"""
    try:
        if 'text_file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo de texto enviado'}), 400
        
        text_file = request.files['text_file']
        model_name = request.form.get('model_name')
        
        if not model_name:
            return jsonify({'error': 'Nome do modelo é obrigatório'}), 400
        
        # Salvar arquivo temporariamente
        model_dir = os.path.join(TRAINING_FOLDER, model_name)
        temp_text_path = os.path.join(model_dir, 'temp_texts.txt')
        text_file.save(temp_text_path)
        
        # Gerar CSV
        import auto_transcription
        audio_dir = os.path.join(model_dir, 'wav')
        output_csv = os.path.join(model_dir, 'metadata.csv')
        
        success = auto_transcription.global_csv_generator.create_from_text_file(
            temp_text_path, audio_dir, output_csv
        )
        
        # Limpar arquivo temporário
        if os.path.exists(temp_text_path):
            os.remove(temp_text_path)
        
        if success:
            return jsonify({'success': True, 'message': 'CSV gerado a partir do arquivo de texto'})
        else:
            return jsonify({'error': 'Falha ao gerar CSV'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_voice', methods=['POST'])
def test_voice():
    try:
        data = request.json
        model_name = data.get('model_name')
        text = data.get('text', 'Este é um teste da voz treinada.')
        
        model_path = os.path.join(MODELS_FOLDER, model_name, f"{model_name}.onnx")
        config_path = os.path.join(MODELS_FOLDER, model_name, f"{model_name}.onnx.json")
        
        if not os.path.exists(model_path):
            return jsonify({'error': 'Modelo ONNX não encontrado'}), 400
        
        if not os.path.exists(config_path):
            return jsonify({'error': 'Configuração do modelo não encontrada'}), 400
        
        # Gerar áudio de teste usando sistema de inferência real
        output_file = f"test_{model_name}_{int(time.time())}.wav"
        output_path = os.path.join('static', 'audio', output_file)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Usar sistema de inferência real
            import piper_inference
            
            tts = piper_inference.PiperTTSInference(model_path, config_path)
            audio = tts.synthesize(text, output_path)
            
            return jsonify({
                'success': True,
                'audio_url': f'/static/audio/{output_file}',
                'message': f'Áudio gerado com sucesso ({len(audio)} amostras)'
            })
            
        except Exception as inference_error:
            # Fallback: tentar usar piper CLI se disponível
            cmd = f'echo "{text}" | piper -m "{model_path}" --output_file "{output_path}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'audio_url': f'/static/audio/{output_file}',
                    'message': 'Áudio gerado usando Piper CLI'
                })
            else:
                return jsonify({
                    'error': f'Erro na síntese: {str(inference_error)}. CLI também falhou: {result.stderr}'
                }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_training_pipeline(model_name, model_dir, language, quality, sample_rate, single_speaker):
    global training_status
    
    training_status.update({
        'is_training': True,
        'current_step': 'Iniciando pré-processamento',
        'progress': 0,
        'log': [],
        'model_name': model_name
    })
    
    try:
        # Importar módulo de treinamento real
        import piper_train_real
        
        # Passo 1: Pré-processamento real
        update_training_status('Executando pré-processamento dos dados', 10)
        
        # Verificar se os arquivos necessários existem
        metadata_file = os.path.join(model_dir, 'metadata.csv')
        wav_dir = os.path.join(model_dir, 'wav')
        
        if not os.path.exists(metadata_file):
            raise Exception("Arquivo metadata.csv não encontrado")
        
        if not os.path.exists(wav_dir):
            raise Exception("Diretório wav/ não encontrado")
        
        # Contar arquivos de áudio
        audio_files = [f for f in os.listdir(wav_dir) if f.endswith(('.wav', '.mp3', '.flac'))]
        if len(audio_files) == 0:
            raise Exception("Nenhum arquivo de áudio encontrado")
        
        update_training_status(f'Encontrados {len(audio_files)} arquivos de áudio', 20)
        
        # Executar pré-processamento real
        config_path = piper_train_real.preprocess_dataset(
            input_dir=model_dir,
            output_dir=model_dir,
            language=language,
            sample_rate=sample_rate,
            single_speaker=single_speaker
        )
        
        update_training_status('Pré-processamento concluído', 30)
        
        # Passo 2: Treinamento real
        update_training_status('Iniciando treinamento do modelo neural', 40)
        
        # Determinar número de épocas baseado na qualidade
        max_epochs = {
            'low': 50,
            'medium': 100,
            'high': 200
        }.get(quality, 100)
        
        # Executar treinamento real com callback de progresso
        def training_callback(step, progress):
            update_training_status(step, progress)
        
        checkpoint_path = piper_train_real.train_model(
            data_dir=model_dir,
            config_path=config_path,
            max_epochs=max_epochs,
            update_callback=training_callback
        )
        
        update_training_status('Treinamento concluído, exportando modelo', 90)
        
        # Passo 3: Exportar modelo real
        final_model_dir = os.path.join(MODELS_FOLDER, model_name)
        os.makedirs(final_model_dir, exist_ok=True)
        
        onnx_path = os.path.join(final_model_dir, f"{model_name}.onnx")
        
        # Exportar para ONNX
        export_success = piper_train_real.export_onnx(checkpoint_path, onnx_path)
        
        if not export_success:
            raise Exception("Falha na exportação do modelo ONNX")
        
        # Copiar configuração
        config_src = os.path.join(model_dir, 'config.json')
        config_dst = os.path.join(final_model_dir, f"{model_name}.onnx.json")
        
        if os.path.exists(config_src):
            shutil.copy2(config_src, config_dst)
        else:
            # Criar configuração básica
            config = {
                "audio": {
                    "sample_rate": sample_rate
                },
                "model": {
                    "type": "vits",
                    "quality": quality
                },
                "inference": {
                    "noise_scale": 0.667,
                    "length_scale": 1.0,
                    "noise_w": 0.8
                },
                "model_name": model_name,
                "language": language,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(config_dst, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        update_training_status('Modelo exportado com sucesso!', 100)
        
    except Exception as e:
        training_status.update({
            'current_step': f'Erro: {str(e)}',
            'progress': 0
        })
        training_status['log'].append(f"ERRO: {str(e)}")
    
    finally:
        training_status['is_training'] = False

def update_training_status(step, progress):
    training_status.update({
        'current_step': step,
        'progress': progress
    })
    training_status['log'].append(f"[{progress}%] {step}")

def get_folder_size(folder_path):
    """Calcula tamanho da pasta em MB"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return round(total_size / (1024 * 1024), 2)  # MB
    except:
        return 0

def run_cloud_export(dataset_name, dataset_path, platform):
    """Executa exportação para nuvem em thread separada"""
    try:
        import cloud_training
        
        cloud_training.update_cloud_status('Iniciando exportação', 10, 
                                         is_exporting=True, platform=platform)
        
        # Criar gerenciador de treinamento em nuvem
        manager = cloud_training.CloudTrainingManager()
        
        cloud_training.update_cloud_status('Criando pacote de treinamento', 30)
        
        # Criar pacote para a plataforma
        package_path = manager.create_training_package(
            model_name=dataset_name,
            model_dir=dataset_path,
            platform=platform
        )
        
        cloud_training.update_cloud_status('Gerando URLs de acesso', 70)
        
        # Gerar URLs específicas da plataforma
        if platform == 'colab':
            notebook_url = manager.get_colab_url(package_path)
        else:
            notebook_url = f"#{platform}_notebook"
        
        cloud_training.update_cloud_status('Exportação concluída', 100,
                                         package_url=f"/download_package/{os.path.basename(package_path)}",
                                         notebook_url=notebook_url)
        
    except Exception as e:
        cloud_training.update_cloud_status(f'Erro: {str(e)}', 0)
    finally:
        cloud_training.cloud_training_status['is_exporting'] = False

def download_model_from_cloud(model_url, model_name):
    """Baixa modelo treinado da nuvem"""
    try:
        import requests
        import zipfile
        import tempfile
        
        print(f"📥 Baixando modelo {model_name} da nuvem...")
        
        # Baixar arquivo ZIP
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        # Salvar temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # Extrair para pasta de modelos
        model_dir = os.path.join(MODELS_FOLDER, model_name)
        os.makedirs(model_dir, exist_ok=True)
        
        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        
        # Limpar arquivo temporário
        os.unlink(temp_path)
        
        print(f"✅ Modelo {model_name} baixado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {e}")

def run_auto_transcription(audio_dir, output_csv, engine, language):
    """Executa transcrição automática em thread separada"""
    try:
        import auto_transcription
        
        def transcription_callback(status):
            # Callback para atualizar progresso (pode ser expandido)
            print(f"📊 Progresso: {status['progress']:.1f}% - {status['current_file']}")
        
        success = auto_transcription.start_auto_transcription(
            audio_dir, output_csv, engine, language, transcription_callback
        )
        
        if success:
            print(f"✅ Transcrição concluída: {output_csv}")
        else:
            print(f"❌ Falha na transcrição automática")
            
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")

@app.route('/upload-googlecolab')
def upload_googlecolab():
    """Página de guia para upload manual no Google Colab"""
    return render_template('Upload_Googlecolab.html')

@app.route('/upload-kaggle')
def upload_kaggle():
    """Página de guia para upload manual no Kaggle"""
    return render_template('Upload_Kaggle.html')

if __name__ == '__main__':
    import argparse
    
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Interface web do Piper TTS')
    parser.add_argument('--no-debug', action='store_true', help='Desativar modo debug')
    args = parser.parse_args()
    
    # Criar diretório para arquivos estáticos
    os.makedirs('static/audio', exist_ok=True)
    
    print("Iniciando interface web do Piper TTS...")
    print("Acesse: http://localhost:5000")
    print("Para parar: Ctrl+C")
    
    app.run(debug=not args.no_debug, host='0.0.0.0', port=5000)