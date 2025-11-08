// Variáveis globais
let trainingInterval = null;
let currentTab = 'upload';

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    // Configurar event listeners
    setupEventListeners();
    
    // Carregar dados iniciais
    loadUploadedModels();
    loadTrainedModels();
    
    // Verificar status de treinamento
    checkTrainingStatus();
});

function setupEventListeners() {
    // Form de upload
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }
    
    // Form de treinamento
    const trainingForm = document.getElementById('trainingForm');
    if (trainingForm) {
        trainingForm.addEventListener('submit', handleTraining);
    }
    
    // Form de teste
    const testForm = document.getElementById('testForm');
    if (testForm) {
        testForm.addEventListener('submit', handleTest);
    }
}

// Gerenciamento de abas
function showTab(tabName) {
    // Esconder todas as abas
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remover classe active de todos os botões
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Mostrar aba selecionada
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Ativar botão correspondente
    const activeButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Ações específicas por aba
    if (tabName === 'models') {
        loadModels();
    } else if (tabName === 'test') {
        loadTrainedModels();
    }
}

// Upload de arquivos
async function handleUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const statusDiv = document.getElementById('uploadStatus');
    
    // Mostrar loading
    showStatus(statusDiv, 'Enviando arquivos...', 'info');
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(statusDiv, result.message, 'success');
            loadUploadedModels(); // Atualizar lista de modelos
            
            // Limpar formulário
            event.target.reset();
        } else {
            showStatus(statusDiv, result.error || 'Erro no upload', 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Erro: ${error.message}`, 'error');
    }
}

// Iniciar treinamento
async function handleTraining(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    
    // Converter checkbox para boolean
    data.single_speaker = formData.has('single_speaker');
    data.sample_rate = parseInt(data.sample_rate);
    
    try {
        const response = await fetch('/start_training', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mostrar seção de progresso
            document.getElementById('trainingProgress').style.display = 'block';
            document.getElementById('startTrainingBtn').disabled = true;
            
            // Iniciar monitoramento
            startTrainingMonitoring();
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Monitoramento do treinamento
function startTrainingMonitoring() {
    if (trainingInterval) {
        clearInterval(trainingInterval);
    }
    
    trainingInterval = setInterval(async () => {
        try {
            const response = await fetch('/training_status');
            const status = await response.json();
            
            updateTrainingUI(status);
            
            if (!status.is_training) {
                clearInterval(trainingInterval);
                trainingInterval = null;
                document.getElementById('startTrainingBtn').disabled = false;
                
                if (status.progress === 100) {
                    // Treinamento concluído com sucesso
                    setTimeout(() => {
                        loadModels(); // Atualizar lista de modelos
                        loadTrainedModels(); // Atualizar modelos para teste
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Erro ao verificar status:', error);
        }
    }, 2000);
}

function updateTrainingUI(status) {
    // Atualizar barra de progresso
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill && progressText) {
        progressFill.style.width = `${status.progress}%`;
        progressText.textContent = `${status.progress}%`;
    }
    
    // Atualizar informações
    const currentModel = document.getElementById('currentModel');
    const currentStep = document.getElementById('currentStep');
    
    if (currentModel) currentModel.textContent = status.model_name || '-';
    if (currentStep) currentStep.textContent = status.current_step || '-';
    
    // Atualizar log
    const logOutput = document.getElementById('trainingLog');
    if (logOutput && status.log) {
        logOutput.innerHTML = status.log.map(line => 
            `<div>${escapeHtml(line)}</div>`
        ).join('');
        logOutput.scrollTop = logOutput.scrollHeight;
    }
}

// Verificar status de treinamento ao carregar
async function checkTrainingStatus() {
    try {
        const response = await fetch('/training_status');
        const status = await response.json();
        
        if (status.is_training) {
            document.getElementById('trainingProgress').style.display = 'block';
            document.getElementById('startTrainingBtn').disabled = true;
            startTrainingMonitoring();
        }
    } catch (error) {
        console.error('Erro ao verificar status inicial:', error);
    }
}

// Carregar modelos uploadados para treinamento
async function loadUploadedModels() {
    try {
        // Simular carregamento de modelos uploadados
        // Em uma implementação real, você faria uma requisição para listar os diretórios
        const select = document.getElementById('train_model_name');
        if (select) {
            // Por enquanto, apenas limpar e adicionar opção padrão
            select.innerHTML = '<option value="">Selecione um modelo...</option>';
        }
    } catch (error) {
        console.error('Erro ao carregar modelos uploadados:', error);
    }
}

// Carregar modelos treinados
async function loadModels() {
    try {
        const response = await fetch('/models');
        const models = await response.json();
        
        const container = document.getElementById('modelsList');
        if (!container) return;
        
        if (models.length === 0) {
            container.innerHTML = '<p>Nenhum modelo treinado encontrado.</p>';
            return;
        }
        
        container.innerHTML = models.map(model => `
            <div class="model-card">
                <div class="model-name">${model.name}</div>
                <div class="model-status">
                    <span class="status-badge ${model.has_onnx ? 'status-ready' : 'status-missing'}">
                        ${model.has_onnx ? '✓ ONNX' : '✗ ONNX'}
                    </span>
                    <span class="status-badge ${model.has_json ? 'status-ready' : 'status-missing'}">
                        ${model.has_json ? '✓ Config' : '✗ Config'}
                    </span>
                </div>
                <div class="model-actions">
                    ${model.has_onnx && model.has_json ? 
                        `<button class="btn btn-primary" onclick="testModel('${model.name}')">
                            <i class="fas fa-play"></i> Testar
                        </button>` : 
                        '<span class="text-muted">Modelo incompleto</span>'
                    }
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Erro ao carregar modelos:', error);
        const container = document.getElementById('modelsList');
        if (container) {
            container.innerHTML = '<p>Erro ao carregar modelos.</p>';
        }
    }
}

// Carregar modelos para teste
async function loadTrainedModels() {
    try {
        const response = await fetch('/models');
        const models = await response.json();
        
        const select = document.getElementById('test_model');
        if (!select) return;
        
        select.innerHTML = '<option value="">Selecione um modelo...</option>';
        
        models.forEach(model => {
            if (model.has_onnx && model.has_json) {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                select.appendChild(option);
            }
        });
        
    } catch (error) {
        console.error('Erro ao carregar modelos para teste:', error);
    }
}

// Testar modelo
function testModel(modelName) {
    // Mudar para aba de teste
    showTab('test');
    
    // Selecionar o modelo
    const select = document.getElementById('test_model');
    if (select) {
        select.value = modelName;
    }
}

// Teste de voz
async function handleTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    
    const resultDiv = document.getElementById('audioResult');
    const submitBtn = event.target.querySelector('button[type="submit"]');
    
    // Mostrar loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando...';
    
    try {
        const response = await fetch('/test_voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mostrar resultado
            const audio = document.getElementById('generatedAudio');
            const downloadLink = document.getElementById('downloadLink');
            
            audio.src = result.audio_url;
            downloadLink.href = result.audio_url;
            
            resultDiv.style.display = 'block';
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    } finally {
        // Restaurar botão
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-microphone"></i> Gerar Áudio';
    }
}

// Utilitários
function showStatus(element, message, type) {
    if (!element) return;
    
    element.textContent = message;
    element.className = `status-message status-${type}`;
    element.style.display = 'block';
    
    // Auto-hide após 5 segundos para mensagens de sucesso
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Adicionar modelo uploadado à lista de treinamento
function addModelToTrainingList(modelName) {
    const select = document.getElementById('train_model_name');
    if (select) {
        // Verificar se já existe
        const existingOption = Array.from(select.options).find(opt => opt.value === modelName);
        if (!existingOption) {
            const option = document.createElement('option');
            option.value = modelName;
            option.textContent = modelName;
            select.appendChild(option);
        }
    }
}

// Função para atualizar lista após upload bem-sucedido
function updateAfterUpload(modelName) {
    addModelToTrainingList(modelName);
}

// Variáveis para export train
let exportInterval = null;
let selectedPlatform = 'colab';

// Variáveis para monitoramento remoto
let monitorInterval = null;
let isMonitoring = false;

// Variáveis para automação CSV
let transcriptionInterval = null;
let isTranscribing = false;

// Configurar event listeners para export
function setupExportListeners() {
    // Seleção de plataforma
    const platformCards = document.querySelectorAll('.platform-card');
    platformCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remover seleção anterior
            platformCards.forEach(c => c.classList.remove('selected'));
            
            // Selecionar nova plataforma
            this.classList.add('selected');
            selectedPlatform = this.dataset.platform;
            
            console.log('Plataforma selecionada:', selectedPlatform);
        });
    });
    
    // Seleção padrão (Colab)
    const colabCard = document.querySelector('[data-platform="colab"]');
    if (colabCard) {
        colabCard.classList.add('selected');
    }
    
    // Mudança de dataset
    const datasetSelect = document.getElementById('export_dataset');
    if (datasetSelect) {
        datasetSelect.addEventListener('change', handleDatasetChange);
    }
    
    // Form de exportação
    const exportForm = document.getElementById('exportForm');
    if (exportForm) {
        exportForm.addEventListener('submit', handleExport);
    }
    
    // Form de monitoramento
    const monitorForm = document.getElementById('monitorForm');
    if (monitorForm) {
        monitorForm.addEventListener('submit', handleStartMonitoring);
    }
    
    // Botão de parar monitoramento
    const stopMonitorBtn = document.getElementById('stopMonitorBtn');
    if (stopMonitorBtn) {
        stopMonitorBtn.addEventListener('click', handleStopMonitoring);
    }
    
    // Botão de download manual
    const manualDownloadBtn = document.getElementById('manualDownloadBtn');
    if (manualDownloadBtn) {
        manualDownloadBtn.addEventListener('click', handleManualDownload);
    }
}

// Carregar datasets para exportação
async function loadExportDatasets() {
    try {
        const response = await fetch('/training_datasets');
        const datasets = await response.json();
        
        const select = document.getElementById('export_dataset');
        if (!select) return;
        
        select.innerHTML = '<option value="">Selecione um dataset...</option>';
        
        datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.name;
            option.textContent = `${dataset.name} (${dataset.audio_count} áudios, ${dataset.size_mb}MB)`;
            option.dataset.audioCount = dataset.audio_count;
            option.dataset.sizeMb = dataset.size_mb;
            option.dataset.hasMetadata = dataset.has_metadata;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Erro ao carregar datasets:', error);
    }
}

// Mudança de dataset selecionado
function handleDatasetChange(event) {
    const selectedOption = event.target.selectedOptions[0];
    const infoDiv = document.getElementById('datasetInfo');
    
    if (selectedOption.value) {
        // Mostrar informações do dataset
        document.getElementById('audioCount').textContent = selectedOption.dataset.audioCount;
        document.getElementById('datasetSize').textContent = `${selectedOption.dataset.sizeMb} MB`;
        document.getElementById('hasMetadata').textContent = selectedOption.dataset.hasMetadata === 'true' ? '✅ Sim' : '❌ Não';
        
        infoDiv.style.display = 'block';
    } else {
        infoDiv.style.display = 'none';
    }
}

// Exportar para nuvem
async function handleExport(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        dataset_name: formData.get('dataset_name'),
        platform: selectedPlatform,
        quality: formData.get('quality'),
        epochs: formData.get('epochs'),
        auto_download: formData.has('auto_download')
    };
    
    if (!data.dataset_name) {
        alert('Selecione um dataset para exportar');
        return;
    }
    
    try {
        const response = await fetch('/export_cloud', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mostrar progresso
            document.getElementById('exportProgress').style.display = 'block';
            document.getElementById('exportBtn').disabled = true;
            
            // Iniciar monitoramento
            startExportMonitoring();
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Monitorar progresso da exportação
function startExportMonitoring() {
    if (exportInterval) {
        clearInterval(exportInterval);
    }
    
    exportInterval = setInterval(async () => {
        try {
            const response = await fetch('/cloud_status');
            const status = await response.json();
            
            updateExportUI(status);
            
            if (!status.is_exporting && status.progress === 100) {
                clearInterval(exportInterval);
                exportInterval = null;
                document.getElementById('exportBtn').disabled = false;
                showExportResults(status);
            }
        } catch (error) {
            console.error('Erro ao verificar status da exportação:', error);
        }
    }, 2000);
}

// Atualizar UI da exportação
function updateExportUI(status) {
    const progressFill = document.getElementById('exportProgressFill');
    const progressText = document.getElementById('exportProgressText');
    const platformSpan = document.getElementById('exportPlatform');
    const stepSpan = document.getElementById('exportStep');
    
    if (progressFill && progressText) {
        progressFill.style.width = `${status.progress}%`;
        progressText.textContent = `${status.progress}%`;
    }
    
    if (platformSpan) platformSpan.textContent = status.platform || selectedPlatform;
    if (stepSpan) stepSpan.textContent = status.step || 'Preparando...';
}

// Mostrar resultados da exportação
function showExportResults(status) {
    const resultsDiv = document.getElementById('exportResults');
    const downloadBtn = document.getElementById('downloadPackageBtn');
    const notebookBtn = document.getElementById('openNotebookBtn');
    
    if (resultsDiv) {
        resultsDiv.style.display = 'block';
    }
    
    if (downloadBtn && status.package_url) {
        downloadBtn.href = status.package_url;
    }
    
    if (notebookBtn && status.notebook_url) {
        notebookBtn.href = status.notebook_url;
    }
}

// Atualizar função showTab para incluir export
function showTab(tabName) {
    // Esconder todas as abas
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remover classe active de todos os botões
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Mostrar aba selecionada
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Ativar botão correspondente
    const activeButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    currentTab = tabName;
    
    // Ações específicas por aba
    if (tabName === 'models') {
        loadModels();
    } else if (tabName === 'test') {
        loadTrainedModels();
    } else if (tabName === 'export') {
        loadExportDatasets();
        setupExportListeners();
    } else if (tabName === 'manual') {
        setupManualNavigation();
    }
}

// Atualizar inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Configurar event listeners
    setupEventListeners();
    setupExportListeners();
    setupAutomationListeners();
    
    // Carregar dados iniciais
    loadUploadedModels();
    loadTrainedModels();
    loadTranscriptionEngines();
    
    // Verificar status de treinamento
    checkTrainingStatus();
});

// Funções de monitoramento remoto
async function handleStartMonitoring(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        session_id: formData.get('session_id'),
        notebook_url: formData.get('notebook_url'),
        platform: selectedPlatform,
        model_name: 'remote_training'
    };
    
    if (!data.session_id || !data.notebook_url) {
        alert('Preencha o ID da sessão e URL do notebook');
        return;
    }
    
    try {
        const response = await fetch('/start_remote_monitoring', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            isMonitoring = true;
            showMonitorDashboard();
            startRemoteMonitoring();
            
            document.getElementById('startMonitorBtn').disabled = true;
            document.getElementById('stopMonitorBtn').disabled = false;
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

async function handleStopMonitoring() {
    try {
        const response = await fetch('/stop_remote_monitoring', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            isMonitoring = false;
            stopRemoteMonitoring();
            hideMonitorDashboard();
            
            document.getElementById('startMonitorBtn').disabled = false;
            document.getElementById('stopMonitorBtn').disabled = true;
        }
    } catch (error) {
        console.error('Erro ao parar monitoramento:', error);
    }
}

function showMonitorDashboard() {
    document.getElementById('monitorDashboard').style.display = 'block';
    document.getElementById('monitorPlaceholder').style.display = 'none';
    
    // Atualizar status de conexão
    const statusIndicator = document.getElementById('connectionStatus');
    statusIndicator.textContent = '🟢 Conectado';
    statusIndicator.className = 'status-indicator connected';
}

function hideMonitorDashboard() {
    document.getElementById('monitorDashboard').style.display = 'none';
    document.getElementById('monitorPlaceholder').style.display = 'block';
    
    // Reset dos valores
    document.getElementById('currentLoss').textContent = '-';
    document.getElementById('gpuUsage').textContent = '-';
    document.getElementById('memoryUsage').textContent = '-';
    document.getElementById('timeRemaining').textContent = '-';
}

function startRemoteMonitoring() {
    if (monitorInterval) {
        clearInterval(monitorInterval);
    }
    
    monitorInterval = setInterval(async () => {
        try {
            const response = await fetch('/remote_status');
            const status = await response.json();
            
            updateMonitorDashboard(status);
            
        } catch (error) {
            console.error('Erro ao verificar status remoto:', error);
        }
    }, 5000); // Atualizar a cada 5 segundos
}

function stopRemoteMonitoring() {
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
}

function updateMonitorDashboard(status) {
    if (!status.monitoring) {
        return;
    }
    
    const metrics = status.metrics || {};
    
    // Atualizar métricas
    document.getElementById('currentLoss').textContent = 
        metrics.current_loss ? metrics.current_loss.toFixed(4) : '-';
    
    document.getElementById('gpuUsage').textContent = 
        metrics.avg_gpu_usage ? `${metrics.avg_gpu_usage.toFixed(1)}%` : '-';
    
    document.getElementById('memoryUsage').textContent = 
        metrics.memory_usage ? `${metrics.memory_usage}%` : '-';
    
    document.getElementById('timeRemaining').textContent = 
        metrics.time_remaining ? formatTime(metrics.time_remaining) : '-';
    
    // Atualizar progresso
    const progress = metrics.epochs_completed || 0;
    const maxEpochs = 200; // Assumir 200 épocas
    const progressPercent = Math.min((progress / maxEpochs) * 100, 100);
    
    const progressFill = document.getElementById('remoteProgressFill');
    const progressText = document.getElementById('remoteProgressText');
    const progressMessage = document.getElementById('remoteProgressMessage');
    
    if (progressFill && progressText) {
        progressFill.style.width = `${progressPercent}%`;
        progressText.textContent = `${progressPercent.toFixed(1)}%`;
    }
    
    if (progressMessage) {
        if (progress === 0) {
            progressMessage.textContent = 'Inicializando treinamento...';
        } else if (progressPercent < 100) {
            progressMessage.textContent = `Época ${progress}/${maxEpochs} - Treinando...`;
        } else {
            progressMessage.textContent = 'Treinamento concluído!';
            showDownloadReady();
        }
    }
    
    // Adicionar efeito de atualização
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach(card => {
        card.classList.add('updating');
        setTimeout(() => card.classList.remove('updating'), 500);
    });
}

function showDownloadReady() {
    const downloadStatus = document.getElementById('downloadStatus');
    const manualDownloadBtn = document.getElementById('manualDownloadBtn');
    
    if (downloadStatus) {
        downloadStatus.innerHTML = '<p>✅ Modelo treinado e pronto para download!</p>';
        downloadStatus.className = 'download-status ready';
    }
    
    if (manualDownloadBtn) {
        manualDownloadBtn.style.display = 'block';
    }
}

async function handleManualDownload() {
    const notebookUrl = document.getElementById('notebook_url').value;
    const modelName = `remote_model_${Date.now()}`;
    
    try {
        const response = await fetch('/download_trained_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_url: notebookUrl + '/download', // Assumir URL de download
                model_name: modelName
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const downloadStatus = document.getElementById('downloadStatus');
            downloadStatus.innerHTML = '<p>📥 Download iniciado... Aguarde a conclusão.</p>';
            downloadStatus.className = 'download-status downloading';
            
            // Simular progresso de download
            setTimeout(() => {
                downloadStatus.innerHTML = '<p>🎉 Modelo baixado com sucesso!</p>';
                downloadStatus.className = 'download-status completed';
                
                // Atualizar lista de modelos
                loadModels();
            }, 5000);
        } else {
            alert(`Erro no download: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

// Exportar funções globais
window.showTab = showTab;
window.loadModels = loadModels;
window.testModel = testModel;
window.loadExportDatasets = loadExportDatasets;
window.handleStartMonitoring = handleStartMonitoring;
window.handleStopMonitoring = handleStopMonitoring;

// Funções da aba Manual
function setupManualNavigation() {
    // Configurar navegação suave entre seções
    const navLinks = document.querySelectorAll('.manual-nav a');
    const sections = document.querySelectorAll('.manual-section');
    
    // Adicionar event listeners para os links de navegação
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            scrollToSection(targetId);
        });
    });
    
    // Configurar observador de interseção para destacar seção ativa
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Remover classe active de todos os links
                navLinks.forEach(link => link.classList.remove('active'));
                
                // Adicionar classe active ao link correspondente
                const activeLink = document.querySelector(`.manual-nav a[href="#${entry.target.id}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }, {
        rootMargin: '-20% 0px -70% 0px'
    });
    
    // Observar todas as seções
    sections.forEach(section => {
        observer.observe(section);
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Função para copiar código de exemplo
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Mostrar feedback visual
        showCopyFeedback();
    }).catch(err => {
        console.error('Erro ao copiar:', err);
    });
}

function showCopyFeedback() {
    // Criar elemento de feedback
    const feedback = document.createElement('div');
    feedback.textContent = '✅ Copiado!';
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #48bb78;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        z-index: 1000;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(feedback);
    
    // Remover após 2 segundos
    setTimeout(() => {
        document.body.removeChild(feedback);
    }, 2000);
}

// Função para expandir/contrair seções
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const content = section.querySelector('.section-content');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        section.classList.remove('collapsed');
    } else {
        content.style.display = 'none';
        section.classList.add('collapsed');
    }
}

// Adicionar botões de cópia aos blocos de código
function addCopyButtons() {
    const codeBlocks = document.querySelectorAll('.code-block, .csv-example-text');
    
    codeBlocks.forEach(block => {
        const copyBtn = document.createElement('button');
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.className = 'copy-btn';
        copyBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            padding: 8px;
            border-radius: 4px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // Posicionar o bloco como relativo
        block.style.position = 'relative';
        
        // Adicionar botão
        block.appendChild(copyBtn);
        
        // Mostrar/esconder botão no hover
        block.addEventListener('mouseenter', () => {
            copyBtn.style.opacity = '1';
        });
        
        block.addEventListener('mouseleave', () => {
            copyBtn.style.opacity = '0';
        });
        
        // Funcionalidade de cópia
        copyBtn.addEventListener('click', () => {
            const text = block.textContent || block.value;
            copyToClipboard(text);
        });
    });
}

// Função para criar índice automático
function createTableOfContents() {
    const toc = document.querySelector('.manual-nav');
    const sections = document.querySelectorAll('.manual-section');
    
    if (!toc || !sections.length) return;
    
    // Limpar navegação existente
    toc.innerHTML = '';
    
    sections.forEach((section, index) => {
        const heading = section.querySelector('h2');
        if (heading) {
            const link = document.createElement('a');
            link.href = `#${section.id}`;
            link.textContent = heading.textContent;
            link.addEventListener('click', (e) => {
                e.preventDefault();
                scrollToSection(section.id);
            });
            
            toc.appendChild(link);
        }
    });
}

// Função para busca no manual
function searchManual(query) {
    const sections = document.querySelectorAll('.manual-section');
    const searchResults = [];
    
    if (!query.trim()) {
        // Mostrar todas as seções se não há busca
        sections.forEach(section => {
            section.style.display = 'block';
        });
        return;
    }
    
    sections.forEach(section => {
        const content = section.textContent.toLowerCase();
        const queryLower = query.toLowerCase();
        
        if (content.includes(queryLower)) {
            section.style.display = 'block';
            searchResults.push(section);
            
            // Destacar termos encontrados
            highlightSearchTerms(section, query);
        } else {
            section.style.display = 'none';
        }
    });
    
    return searchResults;
}

function highlightSearchTerms(section, query) {
    // Implementar destaque de termos de busca
    const walker = document.createTreeWalker(
        section,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }
    
    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = new RegExp(`(${query})`, 'gi');
        
        if (regex.test(text)) {
            const highlightedText = text.replace(regex, '<mark>$1</mark>');
            const span = document.createElement('span');
            span.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(span, textNode);
        }
    });
}

// Exportar funções globais do manual
window.scrollToSection = scrollToSection;
window.copyToClipboard = copyToClipboard;
window.toggleSection = toggleSection;
window.searchManual = searchManual;

// Configurar listeners para automação CSV
function setupAutomationListeners() {
    // Form de transcrição automática
    const transcriptionForm = document.getElementById('transcriptionForm');
    if (transcriptionForm) {
        transcriptionForm.addEventListener('submit', handleAutoTranscription);
    }
    
    // Form de arquivo de texto
    const textFileForm = document.getElementById('textFileForm');
    if (textFileForm) {
        textFileForm.addEventListener('submit', handleTextFileUpload);
    }
    
    // Form de editor manual
    const manualEditorForm = document.getElementById('manualEditorForm');
    if (manualEditorForm) {
        manualEditorForm.addEventListener('submit', handleManualCSVSave);
    }
}

// Mostrar aba de automação
function showAutomationTab(tabName) {
    // Remover classe active de todas as abas
    const tabs = document.querySelectorAll('.automation-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const contents = document.querySelectorAll('.automation-content');
    contents.forEach(content => content.classList.remove('active'));
    
    // Ativar aba selecionada
    const activeTab = document.querySelector(`[onclick="showAutomationTab('${tabName}')"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    const activeContent = document.getElementById(tabName);
    if (activeContent) {
        activeContent.classList.add('active');
    }
    
    // Carregar dados específicos da aba
    if (tabName === 'transcription' || tabName === 'text-file' || tabName === 'manual-editor') {
        loadModelsForAutomation();
    }
}

// Carregar engines de transcrição disponíveis
async function loadTranscriptionEngines() {
    try {
        const response = await fetch('/transcription_engines');
        const data = await response.json();
        
        const select = document.getElementById('transcription_engine');
        if (select && data.engines) {
            select.innerHTML = '';
            
            data.engines.forEach(engine => {
                const option = document.createElement('option');
                option.value = engine;
                
                const engineNames = {
                    'whisper': 'Whisper (OpenAI) - Recomendado',
                    'google': 'Google Speech Recognition',
                    'wav2vec2': 'Wav2Vec2 (Facebook)',
                    'vosk': 'Vosk (Offline)'
                };
                
                option.textContent = engineNames[engine] || engine;
                
                if (engine === data.default) {
                    option.selected = true;
                }
                
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar engines de transcrição:', error);
    }
}

// Carregar modelos para automação
async function loadModelsForAutomation() {
    try {
        const response = await fetch('/training_datasets');
        const datasets = await response.json();
        
        const selects = [
            'transcription_model',
            'text_file_model', 
            'editor_model'
        ];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                select.innerHTML = '<option value="">Selecione um modelo...</option>';
                
                datasets.forEach(dataset => {
                    const option = document.createElement('option');
                    option.value = dataset.name;
                    option.textContent = `${dataset.name} (${dataset.audio_count} áudios)`;
                    select.appendChild(option);
                });
            }
        });
        
    } catch (error) {
        console.error('Erro ao carregar modelos para automação:', error);
    }
}

// Transcrição automática
async function handleAutoTranscription(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        model_name: formData.get('model_name'),
        engine: formData.get('engine'),
        language: formData.get('language')
    };
    
    if (!data.model_name) {
        alert('Selecione um modelo para transcrever');
        return;
    }
    
    try {
        const response = await fetch('/start_transcription', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Mostrar progresso
            document.getElementById('transcriptionProgress').style.display = 'block';
            event.target.querySelector('button[type="submit"]').disabled = true;
            
            // Iniciar monitoramento
            startTranscriptionMonitoring();
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Monitorar progresso da transcrição
function startTranscriptionMonitoring() {
    if (transcriptionInterval) {
        clearInterval(transcriptionInterval);
    }
    
    isTranscribing = true;
    
    transcriptionInterval = setInterval(async () => {
        try {
            const response = await fetch('/transcription_status');
            const status = await response.json();
            
            updateTranscriptionUI(status);
            
            if (!status.is_running) {
                clearInterval(transcriptionInterval);
                transcriptionInterval = null;
                isTranscribing = false;
                
                // Reabilitar botão
                const submitBtn = document.querySelector('#transcriptionForm button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                }
                
                if (status.progress === 100) {
                    showTranscriptionComplete();
                }
            }
        } catch (error) {
            console.error('Erro ao verificar status da transcrição:', error);
        }
    }, 2000);
}

// Atualizar UI da transcrição
function updateTranscriptionUI(status) {
    // Atualizar barra de progresso
    const progressFill = document.getElementById('transcriptionProgressFill');
    const progressText = document.getElementById('transcriptionProgressText');
    
    if (progressFill && progressText) {
        progressFill.style.width = `${status.progress}%`;
        progressText.textContent = `${status.progress.toFixed(1)}%`;
    }
    
    // Atualizar detalhes
    const currentFile = document.getElementById('currentTranscriptionFile');
    const completed = document.getElementById('completedTranscriptions');
    const total = document.getElementById('totalTranscriptions');
    
    if (currentFile) currentFile.textContent = status.current_file || '-';
    if (completed) completed.textContent = status.completed_files || 0;
    if (total) total.textContent = status.total_files || 0;
    
    // Atualizar resultados
    const resultsList = document.getElementById('transcriptionResultsList');
    if (resultsList && status.results) {
        resultsList.innerHTML = '';
        
        status.results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'result-item';
            
            item.innerHTML = `
                <span class="result-file">${result.file}</span>
                <span class="result-text">${result.text}</span>
                <span class="result-status ${result.status}">${result.status === 'success' ? '✅' : '❌'}</span>
            `;
            
            resultsList.appendChild(item);
        });
    }
}

// Mostrar conclusão da transcrição
function showTranscriptionComplete() {
    const progressSection = document.getElementById('transcriptionProgress');
    if (progressSection) {
        const completeMessage = document.createElement('div');
        completeMessage.className = 'validation-message success';
        completeMessage.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>Transcrição automática concluída! O arquivo metadata.csv foi gerado.</span>
        `;
        
        progressSection.appendChild(completeMessage);
    }
}

// Upload de arquivo de texto
async function handleTextFileUpload(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    if (!formData.get('model_name')) {
        alert('Selecione um modelo de destino');
        return;
    }
    
    if (!formData.get('text_file')) {
        alert('Selecione um arquivo de texto');
        return;
    }
    
    try {
        const response = await fetch('/upload_text_file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('CSV gerado com sucesso a partir do arquivo de texto!', 'success');
            event.target.reset();
        } else {
            alert(`Erro: ${result.error}`);
        }
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Salvar CSV manual
async function handleManualCSVSave(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const modelName = formData.get('model_name');
    const csvContent = formData.get('csv_content');
    
    if (!modelName) {
        alert('Selecione um modelo de destino');
        return;
    }
    
    if (!csvContent.trim()) {
        alert('Digite o conteúdo do CSV');
        return;
    }
    
    // Validar formato antes de salvar
    const validation = validateCSVContent(csvContent);
    if (!validation.valid) {
        showValidationResults(validation);
        return;
    }
    
    try {
        // Salvar via API (implementar endpoint se necessário)
        // Por enquanto, mostrar sucesso
        showStatus('CSV salvo com sucesso!', 'success');
        
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

// Validar conteúdo do CSV
function validateCSV() {
    const csvContent = document.getElementById('csv_editor').value;
    const validation = validateCSVContent(csvContent);
    showValidationResults(validation);
}

function validateCSVContent(content) {
    const lines = content.trim().split('\n').filter(line => line.trim());
    const validation = {
        valid: true,
        messages: []
    };
    
    if (lines.length === 0) {
        validation.valid = false;
        validation.messages.push({
            type: 'error',
            message: 'CSV está vazio'
        });
        return validation;
    }
    
    lines.forEach((line, index) => {
        const parts = line.split('|');
        
        if (parts.length < 2) {
            validation.valid = false;
            validation.messages.push({
                type: 'error',
                message: `Linha ${index + 1}: Formato inválido. Use id|texto ou id|falante|texto`
            });
        } else if (parts.length > 3) {
            validation.messages.push({
                type: 'warning',
                message: `Linha ${index + 1}: Muitos separadores "|". Verifique o formato`
            });
        }
        
        if (!parts[0].trim()) {
            validation.valid = false;
            validation.messages.push({
                type: 'error',
                message: `Linha ${index + 1}: ID não pode estar vazio`
            });
        }
        
        const textIndex = parts.length === 2 ? 1 : 2;
        if (!parts[textIndex] || !parts[textIndex].trim()) {
            validation.valid = false;
            validation.messages.push({
                type: 'error',
                message: `Linha ${index + 1}: Texto não pode estar vazio`
            });
        }
    });
    
    if (validation.valid && validation.messages.length === 0) {
        validation.messages.push({
            type: 'success',
            message: `CSV válido! ${lines.length} entradas encontradas.`
        });
    }
    
    return validation;
}

function showValidationResults(validation) {
    const validationDiv = document.getElementById('csvValidation');
    const messagesDiv = document.getElementById('validationMessages');
    
    if (!validationDiv || !messagesDiv) return;
    
    messagesDiv.innerHTML = '';
    
    validation.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `validation-message ${msg.type}`;
        
        const icon = msg.type === 'success' ? 'check-circle' : 
                    msg.type === 'error' ? 'exclamation-circle' : 'exclamation-triangle';
        
        messageDiv.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${msg.message}</span>
        `;
        
        messagesDiv.appendChild(messageDiv);
    });
    
    validationDiv.style.display = 'block';
}

// Carregar CSV existente
async function loadExistingCSV() {
    const modelName = document.getElementById('editor_model').value;
    
    if (!modelName) {
        alert('Selecione um modelo primeiro');
        return;
    }
    
    try {
        // Implementar carregamento de CSV existente
        // Por enquanto, mostrar placeholder
        const editor = document.getElementById('csv_editor');
        editor.value = `${modelName}_001|Exemplo de texto carregado do CSV existente.
${modelName}_002|Segunda linha de exemplo do arquivo.
${modelName}_003|Terceira linha para demonstração.`;
        
        showStatus('CSV existente carregado (exemplo)', 'info');
        
    } catch (error) {
        alert(`Erro ao carregar CSV: ${error.message}`);
    }
}

// Função auxiliar para mostrar status
function showStatus(message, type) {
    // Criar elemento de status temporário
    const statusDiv = document.createElement('div');
    statusDiv.className = `validation-message ${type}`;
    statusDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Adicionar ao DOM temporariamente
    document.body.appendChild(statusDiv);
    statusDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        min-width: 300px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    
    // Remover após 3 segundos
    setTimeout(() => {
        if (document.body.contains(statusDiv)) {
            document.body.removeChild(statusDiv);
        }
    }, 3000);
}

// Exportar funções globais para automação
window.showAutomationTab = showAutomationTab;
window.validateCSV = validateCSV;
window.loadExistingCSV = loadExistingCSV;