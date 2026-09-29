document.addEventListener('DOMContentLoaded', () => {
    const authToken = localStorage.getItem('AUTH_TOKEN');
    const path = window.location.pathname.toLowerCase();
    const isAuthPage = path.endsWith('/login.html') || 
                       path.endsWith('/register.html') || 
                       path.endsWith('/login') || 
                       path.endsWith('/register');

    if (!authToken && !isAuthPage) {
        window.location.replace('/login.html');
        return;
    }

    const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? ''
        : 'https://fineasy.onrender.com';

    const dropZone = document.getElementById('dropZone');
    const pdfInput = document.getElementById('pdfInput');
    const btnBrowse = document.getElementById('btnBrowse');
    const fileInfoCard = document.getElementById('fileInfoCard');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const fileSizeDisplay = document.getElementById('fileSizeDisplay');
    const btnRemoveFile = document.getElementById('btnRemoveFile');
    const btnExtract = document.getElementById('btnExtract');
    const btnSpinner = document.getElementById('btnSpinner');

    const btnSampleManutencao = document.getElementById('btnSampleManutencao');
    const btnSampleInsumos = document.getElementById('btnSampleInsumos');

    const resultsSection = document.getElementById('resultsSection');
    const extractionSourceBadge = document.getElementById('extractionSourceBadge');
    const tabFormattedBtn = document.getElementById('tabFormattedBtn');
    const tabJsonBtn = document.getElementById('tabJsonBtn');
    const tabFormatted = document.getElementById('tabFormatted');
    const tabJson = document.getElementById('tabJson');

    const formattedCategoria = document.getElementById('formattedCategoria');
    const formattedTermos = document.getElementById('formattedTermos');
    const formattedEmitente = document.getElementById('formattedEmitente');
    const formattedFantasia = document.getElementById('formattedFantasia');
    const formattedCnpjEmitente = document.getElementById('formattedCnpjEmitente');
    const formattedDestinatario = document.getElementById('formattedDestinatario');
    const formattedCpfDestinatario = document.getElementById('formattedCpfDestinatario');
    const formattedNumeroNf = document.getElementById('formattedNumeroNf');
    const formattedDataEmissao = document.getElementById('formattedDataEmissao');
    const formattedDataVencimento = document.getElementById('formattedDataVencimento');
    const formattedValorTotal = document.getElementById('formattedValorTotal');
    const formattedParcelas = document.getElementById('formattedParcelas');
    const formattedDescricaoProdutos = document.getElementById('formattedDescricaoProdutos');

    const jsonCodeDisplay = document.getElementById('jsonCodeDisplay');
    const btnCopyJson = document.getElementById('btnCopyJson');
    const btnDownloadJson = document.getElementById('btnDownloadJson');

    const btnConfigModal = document.getElementById('btnConfigModal');
    const apiModal = document.getElementById('apiModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnCancelKey = document.getElementById('btnCancelKey');
    const btnSaveKey = document.getElementById('btnSaveKey');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const btnToggleKey = document.getElementById('btnToggleKey');
    const apiStatusText = document.getElementById('apiStatusText');
    const apiStatusDot = document.getElementById('apiStatusDot');

    let currentSelectedFile = null;
    let latestExtractedJson = null;

    async function checkApiStatus() {
        const savedKey = localStorage.getItem('GEMINI_USER_API_KEY');
        if (savedKey) {
            apiKeyInput.value = savedKey;
            apiStatusDot.classList.add('active');
            apiStatusText.textContent = 'API Gemini: Conectada';
            return;
        }

        try {
            const resp = await fetch(`${API_BASE_URL}/api/status`);
            const data = await resp.json();
            if (data.has_gemini_key) {
                apiStatusDot.classList.add('active');
                apiStatusText.textContent = 'API Gemini: Ativa (.env)';
            } else {
                apiStatusDot.classList.remove('active');
                apiStatusText.textContent = 'API Gemini (Local / Demo)';
            }
        } catch (e) {
            console.warn('Não foi possível verificar status da API:', e);
        }
    }
    checkApiStatus();

    function handleFile(file) {
        if (!file) return;

        if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
            showToast('Por favor, selecione um arquivo no formato PDF.', 'error');
            return;
        }

        currentSelectedFile = file;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);

        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = `${sizeMb} MB`;

        fileInfoCard.classList.remove('hidden');
        btnExtract.disabled = false;
        showToast(`Arquivo "${file.name}" carregado.`, 'info');
    }

    btnBrowse.addEventListener('click', (e) => {
        e.stopPropagation();
        pdfInput.click();
    });

    dropZone.addEventListener('click', () => {
        pdfInput.click();
    });

    pdfInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files[0]) {
            handleFile(dt.files[0]);
        }
    });

    btnRemoveFile.addEventListener('click', () => {
        currentSelectedFile = null;
        pdfInput.value = '';
        fileInfoCard.classList.add('hidden');
        btnExtract.disabled = true;
    });

    async function loadSamplePdf(samplePath, defaultName) {
        try {
            showToast('Carregando arquivo de exemplo...', 'info');
            const resp = await fetch(samplePath);
            if (!resp.ok) throw new Error('Exemplo não encontrado no servidor');
            const blob = await resp.blob();
            const file = new File([blob], defaultName, { type: 'application/pdf' });
            handleFile(file);
        } catch (err) {
            showToast(`Erro ao carregar exemplo: ${err.message}`, 'error');
        }
    }

    btnSampleManutencao.addEventListener('click', () => {
        loadSamplePdf('/sample_notas/nota_fiscal_manutencao_exemplo.pdf', 'NFE-52250913142597000746550010000084381984900945.pdf');
    });

    btnSampleInsumos.addEventListener('click', () => {
        loadSamplePdf('/sample_notas/nota_fiscal_insumos_exemplo.pdf', 'NFE-52260110998877000123550010000054121122334455.pdf');
    });

    btnExtract.addEventListener('click', async () => {
        if (!currentSelectedFile) {
            showToast('Selecione um arquivo PDF antes de extrair.', 'error');
            return;
        }

        btnExtract.disabled = true;
        btnExtract.querySelector('.btn-text').classList.add('hidden');
        btnSpinner.classList.remove('hidden');

        const formData = new FormData();
        formData.append('pdf_file', currentSelectedFile);

        const customKey = localStorage.getItem('GEMINI_USER_API_KEY');
        const headers = {
            'Authorization': `Bearer ${authToken}`
        };
        if (customKey) {
            headers['X-Gemini-Key'] = customKey;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/extract`, {
                method: 'POST',
                headers: headers,
                body: formData
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem('AUTH_TOKEN');
                    localStorage.removeItem('AUTH_USER');
                    showToast('Sessão expirada. Redirecionando para login...', 'error');
                    setTimeout(() => { window.location.replace('/login.html'); }, 1200);
                    return;
                }
                let errorMsg = `Erro ${response.status}: ${response.statusText}`;
                try {
                    const errData = await response.json();
                    errorMsg = errData.error || errorMsg;
                } catch (_) {}
                throw new Error(errorMsg);
            }

            const data = await response.json();
            latestExtractedJson = data;

            renderResults(data);
            showToast('Dados extraídos com sucesso!', 'success');

            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Erro na extração:', error);
            showToast(`Erro: ${error.message}`, 'error');
        } finally {
            btnExtract.disabled = false;
            btnExtract.querySelector('.btn-text').classList.remove('hidden');
            btnSpinner.classList.add('hidden');
        }
    });

    function renderResults(data) {
        resultsSection.classList.remove('hidden');

        if (data._metadados && data._metadados.origem) {
            extractionSourceBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> ${data._metadados.origem}`;
        }

        const classif = data['CLASSIFICAÇÃO'] || data['classificacao'] || {};
        const categoria = classif.categoria || 'Não Classificado';
        const termos = classif.termos_detectados || [];

        formattedCategoria.textContent = categoria;
        formattedTermos.innerHTML = '';
        if (termos.length > 0) {
            termos.forEach(t => {
                const badge = document.createElement('span');
                badge.className = 'tag-badge';
                badge.textContent = t;
                formattedTermos.appendChild(badge);
            });
        } else {
            formattedTermos.innerHTML = '<span class="tag-badge">Nenhum termo específico detectado</span>';
        }

        const fornecedor = data['Fornecedor'] || {};
        const emitente = data['Nome do Emitente'] || fornecedor['Razão Social'] || '-';
        const fantasia = data['Nome Fantasia do Emitente'] || fornecedor['Fantasia'] || emitente;
        const cnpjEmit = data['CNPJ do Emitente'] || fornecedor['CNPJ'] || '-';

        formattedEmitente.textContent = emitente;
        formattedFantasia.textContent = fantasia;
        formattedCnpjEmitente.textContent = cnpjEmit;

        const faturado = data['Faturado'] || {};
        const destNome = data['Nome do Destinatário'] || faturado['Nome Completo'] || '-';
        const destDoc = data['CPF/CNPJ do Destinatário'] || data['CNPJ do Destinatário'] || faturado['CPF'] || '-';

        formattedDestinatario.textContent = destNome;
        formattedCpfDestinatario.textContent = destDoc;

        formattedNumeroNf.textContent = data['Número da Nota Fiscal'] || '-';
        formattedDataEmissao.textContent = data['Data de Emissão'] || '-';
        formattedDataVencimento.textContent = data['Data de Vencimento'] || data['Data de Emissão'] || '-';
        
        let valorTotal = data['Valor Total'] || '0,00';
        if (!valorTotal.includes('R$')) valorTotal = `R$ ${valorTotal}`;
        formattedValorTotal.textContent = valorTotal;

        const parcelas = data['Parcelas'] || {};
        const qtdParcelas = data['Quantidade de Parcelas'] || parcelas['Quantidade de Parcelas'] || 1;
        formattedParcelas.textContent = `${qtdParcelas} parcela(s)`;

        formattedDescricaoProdutos.textContent = data['Descrição dos Produtos'] || 'Descrição não informada no documento.';

        const jsonString = JSON.stringify(data, null, 2);
        jsonCodeDisplay.innerHTML = syntaxHighlightJson(jsonString);
    }

    function syntaxHighlightJson(json) {
        if (!json) return '';
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }

    tabFormattedBtn.addEventListener('click', () => {
        tabFormattedBtn.classList.add('active');
        tabJsonBtn.classList.remove('active');
        tabFormatted.classList.add('active');
        tabJson.classList.remove('active');
    });

    tabJsonBtn.addEventListener('click', () => {
        tabJsonBtn.classList.add('active');
        tabFormattedBtn.classList.remove('active');
        tabJson.classList.add('active');
        tabFormatted.classList.remove('active');
    });

    btnCopyJson.addEventListener('click', async () => {
        if (!latestExtractedJson) return;

        try {
            const rawText = JSON.stringify(latestExtractedJson, null, 2);
            await navigator.clipboard.writeText(rawText);

            const originalHtml = btnCopyJson.innerHTML;
            btnCopyJson.innerHTML = '<i class="fa-solid fa-check"></i> Copiado!';
            btnCopyJson.style.color = '#10b981';

            showToast('JSON copiado para a área de transferência!', 'success');

            setTimeout(() => {
                btnCopyJson.innerHTML = originalHtml;
                btnCopyJson.style.color = '';
            }, 2000);
        } catch (err) {
            showToast('Erro ao copiar JSON.', 'error');
        }
    });

    btnDownloadJson.addEventListener('click', () => {
        if (!latestExtractedJson) return;

        const rawText = JSON.stringify(latestExtractedJson, null, 2);
        const blob = new Blob([rawText], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const nfNum = (latestExtractedJson['Número da Nota Fiscal'] || 'nota_fiscal').replace(/\./g, '');
        a.download = `extracao_nf_${nfNum}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('Download do JSON iniciado.', 'info');
    });

    btnConfigModal.addEventListener('click', () => {
        apiModal.classList.remove('hidden');
    });

    function closeModal() {
        apiModal.classList.add('hidden');
    }

    btnCloseModal.addEventListener('click', closeModal);
    btnCancelKey.addEventListener('click', closeModal);

    apiModal.addEventListener('click', (e) => {
        if (e.target === apiModal) closeModal();
    });

    btnToggleKey.addEventListener('click', () => {
        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            btnToggleKey.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
        } else {
            apiKeyInput.type = 'password';
            btnToggleKey.innerHTML = '<i class="fa-regular fa-eye"></i>';
        }
    });

    btnSaveKey.addEventListener('click', () => {
        const key = apiKeyInput.value.trim();
        if (key) {
            localStorage.setItem('GEMINI_USER_API_KEY', key);
            apiStatusDot.classList.add('active');
            apiStatusText.textContent = 'API Gemini: Conectada';
            showToast('Chave de API salva com sucesso!', 'success');
        } else {
            localStorage.removeItem('GEMINI_USER_API_KEY');
            checkApiStatus();
            showToast('Chave removida. Usando modo local.', 'info');
        }
        closeModal();
    });

    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        let icon = 'fa-circle-info';
        if (type === 'success') icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-circle-exclamation';

        toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            localStorage.removeItem('AUTH_TOKEN');
            localStorage.removeItem('AUTH_USER');
            showToast('Sessão encerrada com sucesso.', 'info');
            setTimeout(() => {
                window.location.replace('/login.html');
            }, 400);
        });
    }
});
