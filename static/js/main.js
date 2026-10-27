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

    const authUser = JSON.parse(localStorage.getItem('AUTH_USER') || '{}');
    const sidebarUserName = document.getElementById('sidebarUserName');
    if (sidebarUserName && authUser.name) {
        sidebarUserName.textContent = authUser.name;
    }

    const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? ''
        : 'https://fineasy.onrender.com';

    // =========================================================================
    // SPA NAVIGATION (SIDEBAR)
    // =========================================================================
    const navItems = document.querySelectorAll('.nav-item');
    const spaViews = document.querySelectorAll('.spa-view');

    function switchView(targetViewId) {
        navItems.forEach(item => {
            if (item.dataset.view === targetViewId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        spaViews.forEach(view => {
            if (view.id === targetViewId) {
                view.classList.add('active');
            } else {
                view.classList.remove('active');
            }
        });
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetView = item.dataset.view;
            if (targetView) {
                switchView(targetView);
            }
        });
    });

    // =========================================================================
    // EXTRATOR DE NOTA FISCAL (ETAPA 1 & ETAPA 2)
    // =========================================================================
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

    // Elementos do Painel de Análise (2ª Etapa)
    const analiseFornecedorNome = document.getElementById('analiseFornecedorNome');
    const analiseFornecedorCnpj = document.getElementById('analiseFornecedorCnpj');
    const badgeFornecedor = document.getElementById('badgeFornecedor');

    const analiseFaturadoNome = document.getElementById('analiseFaturadoNome');
    const analiseFaturadoCpf = document.getElementById('analiseFaturadoCpf');
    const badgeFaturado = document.getElementById('badgeFaturado');

    const analiseDespesaNome = document.getElementById('analiseDespesaNome');
    const badgeDespesa = document.getElementById('badgeDespesa');

    const btnLancarSistema = document.getElementById('btnLancarSistema');
    const launchFeedback = document.getElementById('launchFeedback');
    const launchFeedbackText = document.getElementById('launchFeedbackText');

    let currentSelectedFile = null;
    let latestExtractedJson = null;

    // Configuração da API Modal
    const btnConfigModal = document.getElementById('btnConfigModal');
    const apiModal = document.getElementById('apiModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnCancelKey = document.getElementById('btnCancelKey');
    const btnSaveKey = document.getElementById('btnSaveKey');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const btnToggleKey = document.getElementById('btnToggleKey');
    const apiStatusText = document.getElementById('apiStatusText');
    const apiStatusDot = document.getElementById('apiStatusDot');

    async function checkApiStatus() {
        const savedKey = localStorage.getItem('GEMINI_USER_API_KEY');
        if (savedKey) {
            if (apiKeyInput) apiKeyInput.value = savedKey;
            if (apiStatusDot) apiStatusDot.classList.add('active');
            if (apiStatusText) apiStatusText.textContent = 'API Gemini: Conectada';
            return;
        }

        try {
            const resp = await fetch(`${API_BASE_URL}/api/status`);
            const data = await resp.json();
            if (data.has_gemini_key) {
                if (apiStatusDot) apiStatusDot.classList.add('active');
                if (apiStatusText) apiStatusText.textContent = 'API Gemini: Ativa (.env)';
            } else {
                if (apiStatusDot) apiStatusDot.classList.remove('active');
                if (apiStatusText) apiStatusText.textContent = 'API Gemini (Local / Demo)';
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

    if (btnBrowse) {
        btnBrowse.addEventListener('click', (e) => {
            e.stopPropagation();
            pdfInput.click();
        });
    }

    if (dropZone) {
        dropZone.addEventListener('click', () => pdfInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
    }

    if (pdfInput) {
        pdfInput.addEventListener('change', () => {
            if (pdfInput.files && pdfInput.files.length > 0) {
                handleFile(pdfInput.files[0]);
            }
        });
    }

    if (btnRemoveFile) {
        btnRemoveFile.addEventListener('click', () => {
            currentSelectedFile = null;
            pdfInput.value = '';
            fileInfoCard.classList.add('hidden');
            btnExtract.disabled = true;
            showToast('Arquivo removido.', 'info');
        });
    }

    async function loadSamplePdf(samplePath, filename) {
        try {
            showToast(`Carregando exemplo "${filename}"...`, 'info');
            btnExtract.disabled = true;
            btnSpinner.classList.remove('hidden');

            const resp = await fetch(`${API_BASE_URL}${samplePath}`);
            if (!resp.ok) throw new Error(`Falha ao obter ${filename}`);
            const blob = await resp.blob();
            const file = new File([blob], filename, { type: 'application/pdf' });
            handleFile(file);
        } catch (e) {
            console.error(e);
            showToast(`Erro ao carregar arquivo de teste: ${e.message}`, 'error');
        } finally {
            btnSpinner.classList.add('hidden');
        }
    }

    if (btnSampleManutencao) {
        btnSampleManutencao.addEventListener('click', () => {
            loadSamplePdf('/sample_notas/DANFE_084682.pdf', 'DANFE_084682.pdf');
        });
    }

    if (btnSampleInsumos) {
        btnSampleInsumos.addEventListener('click', () => {
            loadSamplePdf('/sample_notas/DANFE_054121.pdf', 'DANFE_054121.pdf');
        });
    }

    // EXTRAÇÃO E ANÁLISE
    if (btnExtract) {
        btnExtract.addEventListener('click', async () => {
            if (!currentSelectedFile) return;

            btnExtract.disabled = true;
            btnExtract.querySelector('.btn-text').classList.add('hidden');
            btnSpinner.classList.remove('hidden');
            launchFeedback.classList.add('hidden');

            const formData = new FormData();
            formData.append('pdf_file', currentSelectedFile);

            const customKey = localStorage.getItem('GEMINI_USER_API_KEY');
            const headers = { 'Authorization': `Bearer ${authToken}` };
            if (customKey) headers['X-Gemini-Key'] = customKey;

            try {
                const response = await fetch(`${API_BASE_URL}/api/extract`, {
                    method: 'POST',
                    headers: headers,
                    body: formData
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        localStorage.removeItem('AUTH_TOKEN');
                        showToast('Sessão expirada. Faça login novamente.', 'error');
                        setTimeout(() => window.location.replace('/login.html'), 1200);
                        return;
                    }
                    let errorMsg = `Erro ${response.status}`;
                    try {
                        const errData = await response.json();
                        errorMsg = errData.error || errorMsg;
                    } catch (_) {}
                    throw new Error(errorMsg);
                }

                const data = await response.json();
                latestExtractedJson = data;

                renderResults(data);
                await executarAnaliseBanco(data);

                showToast('Nota fiscal extraída e analisada com sucesso!', 'success');
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
    }

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
        formattedDataVencimento.textContent = data['Data de Vencimento'] || '-';
        formattedValorTotal.textContent = `R$ ${data['Valor Total'] || '0,00'}`;

        const qtdParc = data['Quantidade de Parcelas'] || (data['Parcelas'] && data['Parcelas']['Quantidade']) || 1;
        formattedParcelas.textContent = `${qtdParc} parcela(s)`;

        formattedDescricaoProdutos.textContent = data['Descrição dos Produtos'] || 'Nenhum item listado.';
        jsonCodeDisplay.textContent = JSON.stringify(data, null, 2);
    }

    // =========================================================================
    // ANÁLISE DOS DADOS NO BANCO (2ª ETAPA - PÁGINAS 1 E 2 DO PDF)
    // =========================================================================
    async function executarAnaliseBanco(dadosNf) {
        try {
            badgeFornecedor.className = 'status-chip chip-loading';
            badgeFornecedor.textContent = 'CONSULTANDO...';
            badgeFaturado.className = 'status-chip chip-loading';
            badgeFaturado.textContent = 'CONSULTANDO...';
            badgeDespesa.className = 'status-chip chip-loading';
            badgeDespesa.textContent = 'CONSULTANDO...';

            const resp = await fetch(`${API_BASE_URL}/api/analise`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dadosNf)
            });

            if (!resp.ok) throw new Error('Falha ao consultar banco');
            const analise = await resp.json();

            // 1. FORNECEDOR
            analiseFornecedorNome.textContent = analise.fornecedor.razao_social;
            analiseFornecedorCnpj.textContent = analise.fornecedor.cnpj ? `CNPJ: ${analise.fornecedor.cnpj}` : 'CNPJ não informado';
            if (analise.fornecedor.existe) {
                badgeFornecedor.className = 'status-chip chip-found';
                badgeFornecedor.textContent = `EXISTE – ID: ${analise.fornecedor.id}`;
            } else {
                badgeFornecedor.className = 'status-chip chip-not-found';
                badgeFornecedor.textContent = 'NÃO EXISTE';
            }

            // 2. FATURADO
            analiseFaturadoNome.textContent = analise.faturado.nome;
            analiseFaturadoCpf.textContent = analise.faturado.cpf ? `CPF: ${analise.faturado.cpf}` : 'Documento não informado';
            if (analise.faturado.existe) {
                badgeFaturado.className = 'status-chip chip-found';
                badgeFaturado.textContent = `EXISTE – ID: ${analise.faturado.id}`;
            } else {
                badgeFaturado.className = 'status-chip chip-not-found';
                badgeFaturado.textContent = 'NÃO EXISTE';
            }

            // 3. DESPESA
            analiseDespesaNome.textContent = analise.despesa.descricao;
            if (analise.despesa.existe) {
                badgeDespesa.className = 'status-chip chip-found';
                badgeDespesa.textContent = `EXISTE – ID: ${analise.despesa.id}`;
            } else {
                badgeDespesa.className = 'status-chip chip-not-found';
                badgeDespesa.textContent = 'NÃO EXISTE';
            }

        } catch (e) {
            console.error('Erro na análise de banco:', e);
            showToast('Erro ao consultar banco de dados.', 'error');
        }
    }

    // AÇÃO: LANÇAR NO SISTEMA FINANCEIRO (PÁGINA 2 DO PDF)
    if (btnLancarSistema) {
        btnLancarSistema.addEventListener('click', async () => {
            if (!latestExtractedJson) {
                showToast('Nenhum dado de nota fiscal disponível para lançamento.', 'error');
                return;
            }

            btnLancarSistema.disabled = true;
            btnLancarSistema.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Lançando no banco...';

            try {
                const resp = await fetch(`${API_BASE_URL}/api/movimentos/lancar-automatico`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(latestExtractedJson)
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.error || 'Falha ao lançar registro');
                }

                const result = await resp.json();

                // 5. INFORMAR AO USUÁRIO QUE REGISTRO FOI LANÇADO COM SUCESSO.
                launchFeedbackText.textContent = result.message || 'REGISTRO FOI LANÇADO COM SUCESSO.';
                launchFeedback.classList.remove('hidden');
                showToast(result.message || 'REGISTRO FOI LANÇADO COM SUCESSO.', 'success');

                // Atualizar badges imediatamente no painel
                await executarAnaliseBanco(latestExtractedJson);

            } catch (err) {
                console.error(err);
                showToast(`Erro ao lançar: ${err.message}`, 'error');
            } finally {
                btnLancarSistema.disabled = false;
                btnLancarSistema.innerHTML = '<i class="fa-solid fa-file-circle-check"></i> LANÇAR NO SISTEMA FINANCEIRO';
            }
        });
    }

    // Tabs Resultados
    if (tabFormattedBtn && tabJsonBtn) {
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
    }

    if (btnCopyJson) {
        btnCopyJson.addEventListener('click', async () => {
            if (!latestExtractedJson) return;
            try {
                await navigator.clipboard.writeText(JSON.stringify(latestExtractedJson, null, 2));
                showToast('JSON copiado para a área de transferência!', 'success');
            } catch (err) {
                showToast('Erro ao copiar JSON.', 'error');
            }
        });
    }

    if (btnDownloadJson) {
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
    }

    // =========================================================================
    // MÓDULO: MANTER PESSOAS (CRUD UniRV)
    // =========================================================================
    const buscaPessoasInput = document.getElementById('buscaPessoasInput');
    const filtroTipoPessoas = document.getElementById('filtroTipoPessoas');
    const filtroStatusPessoas = document.getElementById('filtroStatusPessoas');
    const btnBuscarPessoas = document.getElementById('btnBuscarPessoas');
    const btnTodosPessoas = document.getElementById('btnTodosPessoas');
    const tabelaPessoasBody = document.getElementById('tabelaPessoasBody');

    const btnNovoPessoa = document.getElementById('btnNovoPessoa');
    const modalPessoa = document.getElementById('modalPessoa');
    const btnCloseModalPessoa = document.getElementById('btnCloseModalPessoa');
    const btnCancelPessoa = document.getElementById('btnCancelPessoa');
    const formPessoa = document.getElementById('formPessoa');
    const modalPessoaTitle = document.getElementById('modalPessoaTitle');
    const pessoaIdInput = document.getElementById('pessoaIdInput');
    const pessoaTipoInput = document.getElementById('pessoaTipoInput');
    const pessoaDocInput = document.getElementById('pessoaDocInput');
    const pessoaNomeInput = document.getElementById('pessoaNomeInput');
    const pessoaFantasiaInput = document.getElementById('pessoaFantasiaInput');
    const pessoaEmailInput = document.getElementById('pessoaEmailInput');
    const pessoaTelefoneInput = document.getElementById('pessoaTelefoneInput');

    let pessoasCache = [];
    let pessoasSortAsc = true;

    async function carregarPessoas(query = '', todos = false) {
        const tipo = filtroTipoPessoas.value;
        const status = filtroStatusPessoas.value;
        const params = new URLSearchParams();

        if (todos) params.append('todos', '1');
        if (query) params.append('q', query);
        if (tipo && tipo !== 'TODOS') params.append('tipo', tipo);
        if (status) params.append('status', status);

        try {
            tabelaPessoasBody.innerHTML = `<tr><td colspan="7" class="table-empty-notice"><i class="fa-solid fa-spinner fa-spin"></i><p>Carregando registros...</p></td></tr>`;
            const resp = await fetch(`${API_BASE_URL}/api/pessoas?${params.toString()}`);
            if (!resp.ok) throw new Error('Falha ao buscar pessoas');
            const data = await resp.json();
            pessoasCache = data;
            renderTabelaPessoas(data);
        } catch (e) {
            console.error(e);
            showToast('Erro ao carregar dados de pessoas.', 'error');
        }
    }

    function renderTabelaPessoas(lista) {
        if (!lista || lista.length === 0) {
            tabelaPessoasBody.innerHTML = `
                <tr>
                    <td colspan="7" class="table-empty-notice">
                        <i class="fa-solid fa-inbox"></i>
                        <p>Nenhum registro encontrado.</p>
                        <span>Tente buscar por outro termo ou clique em <strong>TODOS</strong>.</span>
                    </td>
                </tr>
            `;
            return;
        }

        tabelaPessoasBody.innerHTML = lista.map(p => {
            const isAtivo = p.status === 'ATIVO';
            const badgeClass = isAtivo ? 'badge-status-ativo' : 'badge-status-inativo';
            const actionBtn = isAtivo
                ? `<button type="button" class="btn-action-delete" onclick="window.excluirPessoa(${p.id})" title="Inativar Cadastro"><i class="fa-solid fa-ban"></i> Excluir</button>`
                : `<button type="button" class="btn-action-reactivate" onclick="window.reativarPessoa(${p.id})" title="Reativar Cadastro"><i class="fa-solid fa-rotate-left"></i> Reativar</button>`;

            return `
                <tr>
                    <td><strong>#${p.id}</strong></td>
                    <td><span class="tag-badge">${p.tipo}</span></td>
                    <td>
                        <strong>${p.razao_social_nome}</strong>
                        ${p.fantasia ? `<br><small class="text-muted">${p.fantasia}</small>` : ''}
                    </td>
                    <td><code>${p.cnpj_cpf || '-'}</code></td>
                    <td>
                        ${p.telefone ? `<i class="fa-solid fa-phone"></i> ${p.telefone}<br>` : ''}
                        ${p.email ? `<i class="fa-solid fa-envelope"></i> ${p.email}` : ''}
                    </td>
                    <td><span class="${badgeClass}">${p.status}</span></td>
                    <td class="action-buttons-cell">
                        <button type="button" class="btn-action-edit" onclick="window.editarPessoa(${p.id})" title="Editar"><i class="fa-solid fa-pen"></i> Editar</button>
                        ${actionBtn}
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (btnBuscarPessoas) {
        btnBuscarPessoas.addEventListener('click', () => carregarPessoas(buscaPessoasInput.value.trim(), false));
    }
    if (buscaPessoasInput) {
        buscaPessoasInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') carregarPessoas(buscaPessoasInput.value.trim(), false);
        });
    }
    if (btnTodosPessoas) {
        btnTodosPessoas.addEventListener('click', () => {
            buscaPessoasInput.value = '';
            carregarPessoas('', true);
        });
    }

    // Modais de Pessoa
    function abrirModalPessoa(pessoa = null) {
        formPessoa.reset();
        if (pessoa) {
            modalPessoaTitle.innerHTML = '<i class="fa-solid fa-user-pen"></i> Editar Pessoa';
            pessoaIdInput.value = pessoa.id;
            pessoaTipoInput.value = pessoa.tipo;
            pessoaNomeInput.value = pessoa.razao_social_nome;
            pessoaFantasiaInput.value = pessoa.fantasia || '';
            pessoaDocInput.value = pessoa.cnpj_cpf || '';
            pessoaEmailInput.value = pessoa.email || '';
            pessoaTelefoneInput.value = pessoa.telefone || '';
        } else {
            modalPessoaTitle.innerHTML = '<i class="fa-solid fa-user-plus"></i> Inserir Nova Pessoa';
            pessoaIdInput.value = '';
        }
        modalPessoa.classList.remove('hidden');
    }

    if (btnNovoPessoa) btnNovoPessoa.addEventListener('click', () => abrirModalPessoa());
    if (btnCloseModalPessoa) btnCloseModalPessoa.addEventListener('click', () => modalPessoa.classList.add('hidden'));
    if (btnCancelPessoa) btnCancelPessoa.addEventListener('click', () => modalPessoa.classList.add('hidden'));

    if (formPessoa) {
        formPessoa.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = pessoaIdInput.value;
            const payload = {
                tipo: pessoaTipoInput.value,
                razao_social_nome: pessoaNomeInput.value.trim(),
                fantasia: pessoaFantasiaInput.value.trim(),
                cnpj_cpf: pessoaDocInput.value.trim(),
                email: pessoaEmailInput.value.trim(),
                telefone: pessoaTelefoneInput.value.trim()
            };

            const url = id ? `${API_BASE_URL}/api/pessoas/${id}` : `${API_BASE_URL}/api/pessoas`;
            const method = id ? 'PUT' : 'POST';

            try {
                const resp = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) throw new Error('Falha ao salvar pessoa');
                showToast(id ? 'Pessoa atualizada com sucesso!' : 'Pessoa cadastrada com sucesso!', 'success');
                modalPessoa.classList.add('hidden');
                carregarPessoas('', true);
            } catch (err) {
                showToast(`Erro: ${err.message}`, 'error');
            }
        });
    }

    window.editarPessoa = (id) => {
        const pessoa = pessoasCache.find(p => p.id === id);
        if (pessoa) abrirModalPessoa(pessoa);
    };

    window.excluirPessoa = async (id) => {
        if (!confirm('Deseja realmente inativar este cadastro?')) return;
        try {
            const resp = await fetch(`${API_BASE_URL}/api/pessoas/${id}`, { method: 'DELETE' });
            if (!resp.ok) throw new Error('Falha ao inativar');
            showToast('Cadastro inativado com sucesso!', 'success');
            carregarPessoas(buscaPessoasInput.value.trim(), true);
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    window.reativarPessoa = async (id) => {
        try {
            const resp = await fetch(`${API_BASE_URL}/api/pessoas/${id}/reativar`, { method: 'PATCH' });
            if (!resp.ok) throw new Error('Falha ao reativar');
            showToast('Cadastro reativado com sucesso!', 'success');
            carregarPessoas(buscaPessoasInput.value.trim(), true);
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    // =========================================================================
    // MÓDULO: MANTER CLASSIFICAÇÃO (CRUD UniRV)
    // =========================================================================
    const buscaClassifInput = document.getElementById('buscaClassifInput');
    const filtroTipoClassif = document.getElementById('filtroTipoClassif');
    const filtroStatusClassif = document.getElementById('filtroStatusClassif');
    const btnBuscarClassif = document.getElementById('btnBuscarClassif');
    const btnTodosClassif = document.getElementById('btnTodosClassif');
    const tabelaClassifBody = document.getElementById('tabelaClassifBody');

    const btnNovoClassificacao = document.getElementById('btnNovoClassificacao');
    const modalClassif = document.getElementById('modalClassif');
    const btnCloseModalClassif = document.getElementById('btnCloseModalClassif');
    const btnCancelClassif = document.getElementById('btnCancelClassif');
    const formClassif = document.getElementById('formClassif');
    const modalClassifTitle = document.getElementById('modalClassifTitle');
    const classifIdInput = document.getElementById('classifIdInput');
    const classifTipoInput = document.getElementById('classifTipoInput');
    const classifDescInput = document.getElementById('classifDescInput');

    let classifCache = [];

    async function carregarClassificacoes(query = '', todos = false) {
        const tipo = filtroTipoClassif.value;
        const status = filtroStatusClassif.value;
        const params = new URLSearchParams();

        if (todos) params.append('todos', '1');
        if (query) params.append('q', query);
        if (tipo && tipo !== 'TODOS') params.append('tipo', tipo);
        if (status) params.append('status', status);

        try {
            tabelaClassifBody.innerHTML = `<tr><td colspan="5" class="table-empty-notice"><i class="fa-solid fa-spinner fa-spin"></i><p>Carregando...</p></td></tr>`;
            const resp = await fetch(`${API_BASE_URL}/api/classificacoes?${params.toString()}`);
            if (!resp.ok) throw new Error('Falha ao buscar classificações');
            const data = await resp.json();
            classifCache = data;
            renderTabelaClassif(data);
        } catch (e) {
            console.error(e);
            showToast('Erro ao carregar classificações.', 'error');
        }
    }

    function renderTabelaClassif(lista) {
        if (!lista || lista.length === 0) {
            tabelaClassifBody.innerHTML = `
                <tr>
                    <td colspan="5" class="table-empty-notice">
                        <i class="fa-solid fa-inbox"></i>
                        <p>Nenhuma classificação encontrada.</p>
                        <span>Clique em <strong>TODOS</strong> para listar.</span>
                    </td>
                </tr>
            `;
            return;
        }

        tabelaClassifBody.innerHTML = lista.map(c => {
            const isAtivo = c.status === 'ATIVO';
            const badgeClass = isAtivo ? 'badge-status-ativo' : 'badge-status-inativo';
            const actionBtn = isAtivo
                ? `<button type="button" class="btn-action-delete" onclick="window.excluirClassif(${c.id})"><i class="fa-solid fa-ban"></i> Excluir</button>`
                : `<button type="button" class="btn-action-reactivate" onclick="window.reativarClassif(${c.id})"><i class="fa-solid fa-rotate-left"></i> Reativar</button>`;

            return `
                <tr>
                    <td><strong>#${c.id}</strong></td>
                    <td><span class="tag-badge">${c.tipo}</span></td>
                    <td><strong>${c.descricao}</strong></td>
                    <td><span class="${badgeClass}">${c.status}</span></td>
                    <td class="action-buttons-cell">
                        <button type="button" class="btn-action-edit" onclick="window.editarClassif(${c.id})"><i class="fa-solid fa-pen"></i> Editar</button>
                        ${actionBtn}
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (btnBuscarClassif) btnBuscarClassif.addEventListener('click', () => carregarClassificacoes(buscaClassifInput.value.trim(), false));
    if (btnTodosClassif) btnTodosClassif.addEventListener('click', () => {
        buscaClassifInput.value = '';
        carregarClassificacoes('', true);
    });

    function abrirModalClassif(classif = null) {
        formClassif.reset();
        if (classif) {
            modalClassifTitle.innerHTML = '<i class="fa-solid fa-tag"></i> Editar Classificação';
            classifIdInput.value = classif.id;
            classifTipoInput.value = classif.tipo;
            classifDescInput.value = classif.descricao;
        } else {
            modalClassifTitle.innerHTML = '<i class="fa-solid fa-tag"></i> Inserir Nova Classificação';
            classifIdInput.value = '';
        }
        modalClassif.classList.remove('hidden');
    }

    if (btnNovoClassificacao) btnNovoClassificacao.addEventListener('click', () => abrirModalClassif());
    if (btnCloseModalClassif) btnCloseModalClassif.addEventListener('click', () => modalClassif.classList.add('hidden'));
    if (btnCancelClassif) btnCancelClassif.addEventListener('click', () => modalClassif.classList.add('hidden'));

    if (formClassif) {
        formClassif.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = classifIdInput.value;
            const payload = {
                tipo: classifTipoInput.value,
                descricao: classifDescInput.value.trim()
            };

            const url = id ? `${API_BASE_URL}/api/classificacoes/${id}` : `${API_BASE_URL}/api/classificacoes`;
            const method = id ? 'PUT' : 'POST';

            try {
                const resp = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) throw new Error('Falha ao salvar classificação');
                showToast('Classificação salva com sucesso!', 'success');
                modalClassif.classList.add('hidden');
                carregarClassificacoes('', true);
            } catch (err) {
                showToast(`Erro: ${err.message}`, 'error');
            }
        });
    }

    window.editarClassif = (id) => {
        const item = classifCache.find(c => c.id === id);
        if (item) abrirModalClassif(item);
    };

    window.excluirClassif = async (id) => {
        if (!confirm('Deseja inativar esta classificação?')) return;
        try {
            await fetch(`${API_BASE_URL}/api/classificacoes/${id}`, { method: 'DELETE' });
            showToast('Classificação inativada!', 'success');
            carregarClassificacoes(buscaClassifInput.value.trim(), true);
        } catch (e) {
            showToast('Erro ao inativar', 'error');
        }
    };

    window.reativarClassif = async (id) => {
        try {
            await fetch(`${API_BASE_URL}/api/classificacoes/${id}/reativar`, { method: 'PATCH' });
            showToast('Classificação reativada!', 'success');
            carregarClassificacoes(buscaClassifInput.value.trim(), true);
        } catch (e) {
            showToast('Erro ao reativar', 'error');
        }
    };

    // =========================================================================
    // MÓDULO: REGISTRAR CONTAS (CRUD UniRV)
    // =========================================================================
    const buscaContasInput = document.getElementById('buscaContasInput');
    const filtroTipoContas = document.getElementById('filtroTipoContas');
    const filtroStatusContas = document.getElementById('filtroStatusContas');
    const btnBuscarContas = document.getElementById('btnBuscarContas');
    const btnTodosContas = document.getElementById('btnTodosContas');
    const tabelaContasBody = document.getElementById('tabelaContasBody');

    const btnNovoConta = document.getElementById('btnNovoConta');
    const modalConta = document.getElementById('modalConta');
    const btnCloseModalConta = document.getElementById('btnCloseModalConta');
    const btnCancelConta = document.getElementById('btnCancelConta');
    const formConta = document.getElementById('formConta');
    const contaTipoInput = document.getElementById('contaTipoInput');
    const contaNumDocInput = document.getElementById('contaNumDocInput');
    const contaPessoaSelect = document.getElementById('contaPessoaSelect');
    const contaClassifSelect = document.getElementById('contaClassifSelect');
    const contaValorInput = document.getElementById('contaValorInput');
    const contaDataEmissaoInput = document.getElementById('contaDataEmissaoInput');
    const contaQtdParcelasSelect = document.getElementById('contaQtdParcelasSelect');
    const contaDescInput = document.getElementById('contaDescInput');

    const modalDetalhesConta = document.getElementById('modalDetalhesConta');
    const btnCloseModalDetalhes = document.getElementById('btnCloseModalDetalhes');
    const btnFecharDetalhes = document.getElementById('btnFecharDetalhes');
    const detalhesContaBody = document.getElementById('detalhesContaBody');

    async function carregarContas(query = '', todos = false) {
        const tipo = filtroTipoContas.value;
        const status = filtroStatusContas.value;
        const params = new URLSearchParams();

        if (todos) params.append('todos', '1');
        if (query) params.append('q', query);
        if (tipo && tipo !== 'TODOS') params.append('tipo', tipo);
        if (status) params.append('status', status);

        try {
            tabelaContasBody.innerHTML = `<tr><td colspan="9" class="table-empty-notice"><i class="fa-solid fa-spinner fa-spin"></i><p>Carregando contas...</p></td></tr>`;
            const resp = await fetch(`${API_BASE_URL}/api/contas?${params.toString()}`);
            if (!resp.ok) throw new Error('Falha ao buscar contas');
            const data = await resp.json();
            renderTabelaContas(data);
        } catch (e) {
            console.error(e);
            showToast('Erro ao carregar contas.', 'error');
        }
    }

    function renderTabelaContas(lista) {
        if (!lista || lista.length === 0) {
            tabelaContasBody.innerHTML = `
                <tr>
                    <td colspan="9" class="table-empty-notice">
                        <i class="fa-solid fa-inbox"></i>
                        <p>Nenhuma conta financeira carregada.</p>
                        <span>Utilize a busca acima ou clique em <strong>TODOS</strong> para consultar.</span>
                    </td>
                </tr>
            `;
            return;
        }

        tabelaContasBody.innerHTML = lista.map(c => {
            const isAtivo = c.status === 'ATIVO';
            const badgeClass = isAtivo ? 'badge-status-ativo' : 'badge-status-inativo';
            const valorFmt = parseFloat(c.valor_total || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const pessoaNome = c.fornecedor_nome || c.faturado_nome || 'Não vinculado';

            const actionBtn = isAtivo
                ? `<button type="button" class="btn-action-delete" onclick="window.excluirConta(${c.id})"><i class="fa-solid fa-ban"></i> Excluir</button>`
                : `<button type="button" class="btn-action-reactivate" onclick="window.reativarConta(${c.id})"><i class="fa-solid fa-rotate-left"></i> Reativar</button>`;

            return `
                <tr>
                    <td><strong>#${c.id}</strong></td>
                    <td><span class="tag-badge">${c.tipo === 'APAGAR' ? 'A PAGAR' : 'A RECEBER'}</span></td>
                    <td><strong>${c.numero_documento || 'S/N'}</strong></td>
                    <td>${pessoaNome}</td>
                    <td><strong class="valor-total">${valorFmt}</strong></td>
                    <td><span class="tag-badge">${c.qtd_parcelas || 1} parc.</span></td>
                    <td>${c.proximo_vencimento || '-'}</td>
                    <td><span class="${badgeClass}">${c.status}</span></td>
                    <td class="action-buttons-cell">
                        <button type="button" class="btn-action-view" onclick="window.verDetalhesConta(${c.id})"><i class="fa-solid fa-eye"></i> Detalhes</button>
                        ${actionBtn}
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (btnBuscarContas) btnBuscarContas.addEventListener('click', () => carregarContas(buscaContasInput.value.trim(), false));
    if (btnTodosContas) btnTodosContas.addEventListener('click', () => {
        buscaContasInput.value = '';
        carregarContas('', true);
    });

    // Abrir Modal de Nova Conta e preencher selects de Pessoas e Classificações
    async function abrirModalConta() {
        formConta.reset();
        const hoje = new Date().toISOString().split('T')[0];
        contaDataEmissaoInput.value = hoje;

        contaPessoaSelect.innerHTML = '<option value="">Carregando pessoas...</option>';
        contaClassifSelect.innerHTML = '<option value="">Carregando categorias...</option>';

        modalConta.classList.remove('hidden');

        try {
            const [respPessoas, respClassif] = await Promise.all([
                fetch(`${API_BASE_URL}/api/pessoas?todos=1&status=ATIVO`),
                fetch(`${API_BASE_URL}/api/classificacoes?todos=1&status=ATIVO`)
            ]);

            const pessoas = await respPessoas.json();
            const classifs = await respClassif.json();

            contaPessoaSelect.innerHTML = pessoas.length
                ? pessoas.map(p => `<option value="${p.id}">${p.razao_social_nome} (${p.tipo})</option>`).join('')
                : '<option value="">Nenhuma pessoa cadastrada</option>';

            contaClassifSelect.innerHTML = classifs.length
                ? classifs.map(c => `<option value="${c.id}">${c.descricao} (${c.tipo})</option>`).join('')
                : '<option value="">Nenhuma classificação cadastrada</option>';
        } catch (e) {
            console.error(e);
            showToast('Erro ao carregar listas para formulário de conta.', 'error');
        }
    }

    if (btnNovoConta) btnNovoConta.addEventListener('click', abrirModalConta);
    if (btnCloseModalConta) btnCloseModalConta.addEventListener('click', () => modalConta.classList.add('hidden'));
    if (btnCancelConta) btnCancelConta.addEventListener('click', () => modalConta.classList.add('hidden'));

    if (formConta) {
        formConta.addEventListener('submit', async (e) => {
            e.preventDefault();
            const tipo = contaTipoInput.value;
            const valorTotal = parseFloat(contaValorInput.value);
            const qtdParcelas = parseInt(contaQtdParcelasSelect.value, 10);
            const dataEmissao = contaDataEmissaoInput.value;
            const pessoaId = parseInt(contaPessoaSelect.value, 10);
            const classifId = parseInt(contaClassifSelect.value, 10);

            // Gerar parcelas com datas de vencimento mensalmente distintas
            const parcelas = [];
            const valorParcela = valorTotal / qtdParcelas;
            const emissaoDate = dataEmissao ? new Date(dataEmissao + 'T00:00:00') : new Date();

            for (let i = 1; i <= qtdParcelas; i++) {
                const vencDate = new Date(emissaoDate);
                vencDate.setMonth(vencDate.getMonth() + i);
                const vencStr = vencDate.toLocaleDateString('pt-BR');
                parcelas.push({
                    numero_parcela: i,
                    data_vencimento: vencStr,
                    valor: valorParcela
                });
            }

            const payload = {
                tipo: tipo,
                numero_documento: contaNumDocInput.value.trim(),
                descricao: contaDescInput.value.trim() || `Lançamento ${tipo}`,
                data_emissao: dataEmissao ? new Date(dataEmissao + 'T00:00:00').toLocaleDateString('pt-BR') : '',
                valor_total: valorTotal,
                pessoa_fornecedor_id: tipo === 'APAGAR' ? pessoaId : null,
                pessoa_faturado_id: tipo === 'ARECEBER' ? pessoaId : null,
                classificacoes: [{ classificacao_id: classifId, valor: valorTotal }],
                parcelas: parcelas
            };

            try {
                const resp = await fetch(`${API_BASE_URL}/api/contas`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!resp.ok) throw new Error('Falha ao registrar conta');
                showToast('Conta registrada com sucesso!', 'success');
                modalConta.classList.add('hidden');
                carregarContas('', true);
            } catch (err) {
                showToast(`Erro: ${err.message}`, 'error');
            }
        });
    }

    window.verDetalhesConta = async (id) => {
        try {
            detalhesContaBody.innerHTML = '<p><i class="fa-solid fa-spinner fa-spin"></i> Carregando detalhes...</p>';
            modalDetalhesConta.classList.remove('hidden');

            const resp = await fetch(`${API_BASE_URL}/api/contas/${id}`);
            if (!resp.ok) throw new Error('Falha ao obter detalhes');
            const conta = await resp.json();

            const valorFmt = parseFloat(conta.valor_total || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const parcelasHtml = (conta.parcelas || []).map(p => `
                <tr>
                    <td><strong>${p.identificacao}</strong></td>
                    <td>${p.data_vencimento}</td>
                    <td><strong>${parseFloat(p.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</strong></td>
                    <td><span class="tag-badge">${p.status_pagamento}</span></td>
                </tr>
            `).join('');

            const classifsHtml = (conta.classificacoes || []).map(c => `
                <span class="tag-badge"><i class="fa-solid fa-tag"></i> ${c.descricao} (${c.classificacao_tipo})</span>
            `).join(' ');

            detalhesContaBody.innerHTML = `
                <div style="margin-bottom: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                        <h4 style="font-size: 1.2rem; color: var(--text-primary); font-weight: 700;">
                            ${conta.tipo === 'APAGAR' ? 'Conta a Pagar' : 'Conta a Receber'} - Doc: ${conta.numero_documento}
                        </h4>
                        <span class="tag-badge" style="font-size: 0.9rem;">${valorFmt}</span>
                    </div>
                    <p style="color: var(--text-secondary); margin-bottom: 0.5rem;">
                        <strong>Pessoa:</strong> ${conta.fornecedor_nome || conta.faturado_nome || 'N/A'}
                    </p>
                    <p style="color: var(--text-secondary); margin-bottom: 0.5rem;">
                        <strong>Histórico:</strong> ${conta.descricao || 'Sem descrição'}
                    </p>
                    <div style="margin-top: 0.75rem;">
                        <strong>Classificações:</strong> ${classifsHtml || 'Nenhuma'}
                    </div>
                </div>

                <h5 style="margin-bottom: 0.75rem; color: var(--text-primary); font-weight: 700;">
                    <i class="fa-solid fa-calendar-days"></i> Parcelas do Movimento (${(conta.parcelas || []).length})
                </h5>
                <table class="data-table" style="font-size: 0.85rem;">
                    <thead>
                        <tr>
                            <th>Parcela</th>
                            <th>Vencimento</th>
                            <th>Valor</th>
                            <th>Status Pagamento</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${parcelasHtml}
                    </tbody>
                </table>
            `;
        } catch (e) {
            detalhesContaBody.innerHTML = `<p style="color: red;">Erro ao carregar detalhes: ${e.message}</p>`;
        }
    };

    if (btnCloseModalDetalhes) btnCloseModalDetalhes.addEventListener('click', () => modalDetalhesConta.classList.add('hidden'));
    if (btnFecharDetalhes) btnFecharDetalhes.addEventListener('click', () => modalDetalhesConta.classList.add('hidden'));

    window.excluirConta = async (id) => {
        if (!confirm('Deseja realmente inativar esta conta e suas parcelas?')) return;
        try {
            await fetch(`${API_BASE_URL}/api/contas/${id}`, { method: 'DELETE' });
            showToast('Conta inativada com sucesso!', 'success');
            carregarContas(buscaContasInput.value.trim(), true);
        } catch (e) {
            showToast('Erro ao inativar conta', 'error');
        }
    };

    window.reativarConta = async (id) => {
        try {
            await fetch(`${API_BASE_URL}/api/contas/${id}/reativar`, { method: 'PATCH' });
            showToast('Conta reativada com sucesso!', 'success');
            carregarContas(buscaContasInput.value.trim(), true);
        } catch (e) {
            showToast('Erro ao reativar conta', 'error');
        }
    };

    // Ordenação clicável de colunas nas tabelas
    document.querySelectorAll('.data-table th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => !r.querySelector('.table-empty-notice'));
            if (rows.length === 0) return;

            const colIndex = Array.from(th.parentNode.children).indexOf(th);
            const isAsc = !th.classList.contains('asc');

            table.querySelectorAll('th').forEach(header => {
                header.classList.remove('asc', 'desc');
                const icon = header.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-sort';
            });

            th.classList.add(isAsc ? 'asc' : 'desc');
            const thIcon = th.querySelector('i');
            if (thIcon) thIcon.className = isAsc ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down';

            rows.sort((rowA, rowB) => {
                const cellA = rowA.children[colIndex].textContent.trim();
                const cellB = rowB.children[colIndex].textContent.trim();
                return isAsc ? cellA.localeCompare(cellB, undefined, { numeric: true }) : cellB.localeCompare(cellA, undefined, { numeric: true });
            });

            rows.forEach(r => tbody.appendChild(r));
        });
    });

    // =========================================================================
    // MODAL DE CHAVE GEMINI & TOASTS
    // =========================================================================
    if (btnConfigModal) btnConfigModal.addEventListener('click', () => apiModal.classList.remove('hidden'));
    function fecharModalApi() { apiModal.classList.add('hidden'); }
    if (btnCloseModal) btnCloseModal.addEventListener('click', fecharModalApi);
    if (btnCancelKey) btnCancelKey.addEventListener('click', fecharModalApi);

    if (apiModal) {
        apiModal.addEventListener('click', (e) => {
            if (e.target === apiModal) fecharModalApi();
        });
    }

    if (btnToggleKey) {
        btnToggleKey.addEventListener('click', () => {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                btnToggleKey.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
            } else {
                apiKeyInput.type = 'password';
                btnToggleKey.innerHTML = '<i class="fa-regular fa-eye"></i>';
            }
        });
    }

    if (btnSaveKey) {
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
                showToast('Chave removida. Usando modo padrão.', 'info');
            }
            fecharModalApi();
        });
    }

    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
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
            setTimeout(() => window.location.replace('/login.html'), 400);
        });
    }
});
