/**
 * AI LUẬT SƯ — Client Application Logic (Vanilla JS)
 * Hỗ trợ 3 Chế độ:
 * 1. Tư Vấn Pháp Lý 4 Bước (Chat Q&A)
 * 2. Rà Soát & Thẩm Định Hợp Đồng (Contract Reviewer)
 * 3. Phiên Tòa Giả Lập & Đối Chất Tranh Tụng (AI Moot Court)
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements: Navigation & Modes ---
    const sidebar = document.getElementById('sidebar');
    const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    const modeChatBtn = document.getElementById('mode-chat');
    const modeReviewBtn = document.getElementById('mode-review');
    const modeCourtBtn = document.getElementById('mode-court');
    const modeNegotiateBtn = document.getElementById('mode-negotiate');
    const modePetitionBtn = document.getElementById('mode-petition');
    const modeAuditorBtn = document.getElementById('mode-auditor');
    const viewChat = document.getElementById('view-chat');
    const viewReview = document.getElementById('view-review');
    const viewCourt = document.getElementById('view-court');
    const viewNegotiate = document.getElementById('view-negotiate');
    const viewPetition = document.getElementById('view-petition');
    const viewAuditor = document.getElementById('view-auditor');
    const btnOpenCalc = document.getElementById('btn-open-calc');
    const calcModal = document.getElementById('calc-modal');
    const btnCloseCalc = document.getElementById('btn-close-calc');
    const sidebarCategoriesSection = document.getElementById('sidebar-categories-section');
    const btnNewChat = document.getElementById('btn-new-chat');
    const btnNewChatText = document.getElementById('btn-new-chat-text');
    const currentCategoryDisplay = document.getElementById('current-category-display');
    const modelBadge = document.getElementById('model-badge');

    // --- DOM Elements: View 1 (Chat) ---
    const categoryListEl = document.getElementById('category-list');
    const historyListEl = document.getElementById('history-list');
    const welcomeScreen = document.getElementById('welcome-screen');
    const quickPromptsGrid = document.getElementById('quick-prompts-grid');
    const messagesList = document.getElementById('messages-list');
    const userInput = document.getElementById('user-input');
    const btnSend = document.getElementById('btn-send');
    const chatContainer = document.getElementById('chat-container');
    const btnChatAttach = document.getElementById('btn-chat-attach');
    const chatFileInput = document.getElementById('chat-file-input');
    const btnVoiceInput = document.getElementById('btn-voice-input');

    // --- DOM Elements: View 2 (Contract Review) ---
    const contractDropzone = document.getElementById('contract-dropzone');
    const contractFileInput = document.getElementById('contract-file-input');
    const dropzoneDefault = document.getElementById('dropzone-default');
    const dropzoneSelected = document.getElementById('dropzone-selected');
    const selectedFileName = document.getElementById('selected-file-name');
    const selectedFileSize = document.getElementById('selected-file-size');
    const btnRemoveFile = document.getElementById('btn-remove-file');
    const partyRoleSelect = document.getElementById('party-role');
    const focusAreasInput = document.getElementById('focus-areas');
    const btnToggleText = document.getElementById('btn-toggle-text');
    const contractManualText = document.getElementById('contract-manual-text');
    const btnStartReview = document.getElementById('btn-start-review');
    const reviewLoading = document.getElementById('review-loading');
    const reviewResultCard = document.getElementById('review-result-card');
    const resultDocName = document.getElementById('result-doc-name');
    const resultModelBadge = document.getElementById('result-model-badge');
    const resultContent = document.getElementById('result-content');
    const btnCopyResult = document.getElementById('btn-copy-result');
    const btnPrintResult = document.getElementById('btn-print-result');
    const btnExportDocx = document.getElementById('btn-export-docx');

    // --- DOM Elements: View 3 (Moot Court) ---
    const courtSetupCard = document.getElementById('court-setup-card');
    const presetCasesGrid = document.getElementById('preset-cases-grid');
    const customCaseTitle = document.getElementById('custom-case-title');
    const customCaseFacts = document.getElementById('custom-case-facts');
    const customUserRole = document.getElementById('custom-user-role');
    const btnEnterCourt = document.getElementById('btn-enter-court');
    const courtArena = document.getElementById('court-arena');
    const arenaCaseTitle = document.getElementById('arena-case-title');
    const arenaUserRole = document.getElementById('arena-user-role');
    const meterScoreText = document.getElementById('meter-score-text');
    const meterBarFill = document.getElementById('meter-bar-fill');
    const btnRequestVerdict = document.getElementById('btn-request-verdict');
    const arenaTranscript = document.getElementById('arena-transcript');
    const arenaUserInput = document.getElementById('arena-user-input');
    const btnCourtSend = document.getElementById('btn-court-send');
    const courtVerdictCard = document.getElementById('court-verdict-card');
    const verdictContent = document.getElementById('verdict-content');
    const btnCopyVerdict = document.getElementById('btn-copy-verdict');
    const btnReplayCourt = document.getElementById('btn-replay-court');
    const btnExportVerdictDocx = document.getElementById('btn-export-verdict-docx');
    const btnNegVoice = document.getElementById('btn-neg-voice');

    // --- DOM Elements: Settings Modal ---
    const btnOpenSettings = document.getElementById('btn-open-settings');
    const settingsModal = document.getElementById('settings-modal');
    const btnCloseModal = document.getElementById('btn-close-settings') || document.getElementById('btn-close-modal');
    const inputApiKey = document.getElementById('input-api-key');
    const btnTogglePwd = document.getElementById('btn-toggle-pwd');
    const selectModel = document.getElementById('select-model');
    const btnSaveSettings = document.getElementById('btn-save-settings');
    const btnClearKey = document.getElementById('btn-clear-key');
    const apiStatusDot = document.getElementById('api-status-dot');

    // --- DOM Elements: Law Inspector Modal & Quick Search ---
    const lawModal = document.getElementById('law-modal');
    const btnCloseLawModal = document.getElementById('btn-close-law-modal');
    const btnCloseLawBottom = document.getElementById('btn-close-law-bottom');
    const lawModalTitle = document.getElementById('law-modal-title');
    const lawModalSub = document.getElementById('law-modal-sub');
    const lawFullText = document.getElementById('law-full-text');
    const lawOfficialLink = document.getElementById('law-official-link');
    const sidebarLawSearch = document.getElementById('sidebar-law-search');
    const btnSidebarLawSearch = document.getElementById('btn-sidebar-law-search');

    // --- Application State ---
    let currentMode = 'chat'; // 'chat' | 'review' | 'court' | 'negotiate' | 'petition' | 'auditor'
    let categories = [];
    let currentCategory = { id: 'all', name: 'Tư vấn Tổng hợp', icon: '⚖️' };
    let currentSessionId = generateId();
    let currentHistory = [];
    let allSessions = loadSessions();
    let selectedContractFile = null;
    let lastReviewRawText = '';
    let lastReviewCitations = [];

    // Moot Court State
    let courtPresets = [];
    let activeCourtCase = null;
    let courtDialogueHistory = []; // [ { speaker: 'user'|'opposing'|'judge', text: string } ]
    let currentPersuasionScore = 50;
    let lastVerdictMarkdown = '';

    // Negotiation State
    let negotiatePresets = [];
    let activeNegotiateScenario = null;
    let negotiateHistory = [];
    let lastRecommendedCounter = '';

    // Petition State
    let lastPetitionMarkdown = '';
    let lastPetitionTitle = '';

    // Corporate Audit State
    let lastCorporateData = null;

    // --- Initialize ---
    init();

    async function init() {
        bindEvents();
        loadSavedSettings();
        await fetchCategories();
        await fetchCourtPresets();
        renderHistory();
        checkBackendHealth();
    }

    function bindEvents() {
        // Toggle Sidebar
        btnToggleSidebar.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });

        // 6 Navigation Modes
        modeChatBtn.addEventListener('click', () => switchMode('chat'));
        modeReviewBtn.addEventListener('click', () => switchMode('review'));
        modeCourtBtn.addEventListener('click', () => switchMode('court'));
        if (modeNegotiateBtn) modeNegotiateBtn.addEventListener('click', () => switchMode('negotiate'));
        if (modePetitionBtn) modePetitionBtn.addEventListener('click', () => switchMode('petition'));
        if (modeAuditorBtn) modeAuditorBtn.addEventListener('click', () => switchMode('auditor'));

        if (btnExportVerdictDocx) {
            btnExportVerdictDocx.addEventListener('click', downloadCourtVerdictDocx);
        }

        // Voice inputs
        initSpeechRecognition(btnVoiceInput, userInput);
        if (btnNegVoice) {
            initSpeechRecognition(btnNegVoice, document.getElementById('neg-user-input'));
        }

        // Negotiation Arena Events
        const btnStartNeg = document.getElementById('btn-start-negotiate');
        if (btnStartNeg) btnStartNeg.addEventListener('click', startNegotiationSession);

        const btnExitNeg = document.getElementById('btn-exit-negotiate');
        if (btnExitNeg) {
            btnExitNeg.addEventListener('click', () => {
                document.getElementById('negotiate-setup-card').style.display = 'block';
                document.getElementById('negotiate-arena').style.display = 'none';
            });
        }

        const btnNegSend = document.getElementById('btn-neg-send');
        if (btnNegSend) btnNegSend.addEventListener('click', sendNegotiateTurn);

        const negInput = document.getElementById('neg-user-input');
        if (negInput) {
            negInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendNegotiateTurn();
                }
            });
        }

        const recChip = document.getElementById('neg-recommended-chip');
        if (recChip) {
            recChip.addEventListener('click', () => {
                if (lastRecommendedCounter && negInput) {
                    negInput.value = lastRecommendedCounter;
                    negInput.focus();
                }
            });
        }

        // Initialize sub-modules
        initCalculatorModal();
        initPetitionGenerator();
        initAuditor();

        // New Session Button
        btnNewChat.addEventListener('click', handleNewSession);

        // Chat Composer Input
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
            btnSend.disabled = !userInput.value.trim();
        });

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!btnSend.disabled) sendMessage();
            }
        });

        btnSend.addEventListener('click', sendMessage);

        btnChatAttach.addEventListener('click', () => chatFileInput.click());
        chatFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                const file = e.target.files[0];
                switchMode('review');
                setContractFile(file);
            }
        });

        // Contract Review Drag & Drop
        contractDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            contractDropzone.classList.add('dragover');
        });

        contractDropzone.addEventListener('dragleave', () => {
            contractDropzone.classList.remove('dragover');
        });

        contractDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            contractDropzone.classList.remove('dragover');
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                setContractFile(e.dataTransfer.files[0]);
            }
        });

        contractDropzone.addEventListener('click', (e) => {
            if (e.target !== btnRemoveFile && !btnRemoveFile.contains(e.target)) {
                contractFileInput.click();
            }
        });

        contractFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                setContractFile(e.target.files[0]);
            }
        });

        btnRemoveFile.addEventListener('click', (e) => {
            e.stopPropagation();
            clearContractFile();
        });

        btnToggleText.addEventListener('click', () => {
            const isHidden = contractManualText.style.display === 'none';
            contractManualText.style.display = isHidden ? 'block' : 'none';
            btnToggleText.textContent = isHidden 
                ? 'Ẩn ô dán văn bản ▲' 
                : 'Hoặc dán trực tiếp điều khoản hợp đồng dạng văn bản ▼';
        });

        btnStartReview.addEventListener('click', startContractReview);

        btnCopyResult.addEventListener('click', () => {
            if (lastReviewRawText) {
                navigator.clipboard.writeText(lastReviewRawText);
                btnCopyResult.textContent = '✅ Đã sao chép!';
                setTimeout(() => btnCopyResult.textContent = '📋 Sao chép', 2000);
            }
        });

        btnPrintResult.addEventListener('click', () => window.print());

        if (btnExportDocx) {
            btnExportDocx.addEventListener('click', downloadContractDocx);
        }

        // Moot Court Events
        btnEnterCourt.addEventListener('click', enterCourtArena);

        arenaUserInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendCourtArgument();
            }
        });

        btnCourtSend.addEventListener('click', sendCourtArgument);

        // Quick Rebuttal Chips
        document.querySelectorAll('.rebuttal-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const text = chip.getAttribute('data-text');
                arenaUserInput.value = text;
                arenaUserInput.focus();
            });
        });

        btnRequestVerdict.addEventListener('click', requestCourtVerdict);

        btnCopyVerdict.addEventListener('click', () => {
            const verdictText = verdictContent.innerText;
            navigator.clipboard.writeText(verdictText);
            btnCopyVerdict.textContent = '✅ Đã sao chép!';
            setTimeout(() => btnCopyVerdict.textContent = '📋 Sao chép Bản Án', 2000);
        });

        btnReplayCourt.addEventListener('click', resetCourtroom);

        // Settings Modal
        btnOpenSettings.addEventListener('click', () => {
            inputApiKey.value = localStorage.getItem('ai_lawyer_api_key') || '';
            if (selectModel) selectModel.value = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';
            settingsModal.classList.add('open');
        });

        if (btnCloseModal) {
            btnCloseModal.addEventListener('click', () => settingsModal.classList.remove('open'));
        }
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) settingsModal.classList.remove('open');
        });

        btnTogglePwd.addEventListener('click', () => {
            inputApiKey.type = inputApiKey.type === 'password' ? 'text' : 'password';
            btnTogglePwd.textContent = inputApiKey.type === 'password' ? '👁️' : '🔒';
        });

        btnSaveSettings.addEventListener('click', () => {
            const key = inputApiKey.value.trim();
            const model = selectModel ? selectModel.value : 'gemini-2.5-flash';
            if (key) {
                localStorage.setItem('ai_lawyer_api_key', key);
            } else {
                localStorage.removeItem('ai_lawyer_api_key');
            }
            localStorage.setItem('ai_lawyer_model', model);
            settingsModal.classList.remove('open');
            checkBackendHealth();
        });

        btnClearKey.addEventListener('click', () => {
            localStorage.removeItem('ai_lawyer_api_key');
            inputApiKey.value = '';
            checkBackendHealth();
        });

        // Law Inspector Modal Events
        btnCloseLawModal.addEventListener('click', () => lawModal.classList.remove('open'));
        btnCloseLawBottom.addEventListener('click', () => lawModal.classList.remove('open'));
        lawModal.addEventListener('click', (e) => {
            if (e.target === lawModal) lawModal.classList.remove('open');
        });

        // Sidebar Quick Law Search
        btnSidebarLawSearch.addEventListener('click', handleSidebarLawSearch);
        sidebarLawSearch.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSidebarLawSearch();
            }
        });
    }

    // --- Mode Switching (6 Modes) ---
    function switchMode(mode) {
        currentMode = mode;
        [modeChatBtn, modeReviewBtn, modeCourtBtn, modeNegotiateBtn, modePetitionBtn, modeAuditorBtn].forEach(b => { if (b) b.classList.remove('active'); });
        [viewChat, viewReview, viewCourt, viewNegotiate, viewPetition, viewAuditor].forEach(v => { if (v) v.classList.remove('active'); });

        if (mode === 'chat') {
            modeChatBtn.classList.add('active');
            viewChat.classList.add('active');
            sidebarCategoriesSection.style.display = 'block';
            btnNewChatText.textContent = 'Phiên tư vấn mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">${currentCategory.icon}</span><h1 class="cat-title">${currentCategory.name}</h1>`;
        } else if (mode === 'review') {
            modeReviewBtn.classList.add('active');
            viewReview.classList.add('active');
            sidebarCategoriesSection.style.display = 'none';
            btnNewChatText.textContent = 'Hợp đồng mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">📑</span><h1 class="cat-title">Rà Soát & Thẩm Định Hợp Đồng</h1>`;
        } else if (mode === 'court') {
            modeCourtBtn.classList.add('active');
            viewCourt.classList.add('active');
            sidebarCategoriesSection.style.display = 'none';
            btnNewChatText.textContent = 'Vụ án mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">🔨</span><h1 class="cat-title">Đấu Trường Phiên Tòa Giả Lập</h1>`;
        } else if (mode === 'negotiate') {
            if (modeNegotiateBtn) modeNegotiateBtn.classList.add('active');
            if (viewNegotiate) viewNegotiate.classList.add('active');
            sidebarCategoriesSection.style.display = 'none';
            btnNewChatText.textContent = 'Đàm phán mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">🤝</span><h1 class="cat-title">Huấn Luyện Viên Đàm Phán & Hòa Giải Giả Lập</h1>`;
            fetchNegotiatePresets();
        } else if (mode === 'petition') {
            if (modePetitionBtn) modePetitionBtn.classList.add('active');
            if (viewPetition) viewPetition.classList.add('active');
            sidebarCategoriesSection.style.display = 'none';
            btnNewChatText.textContent = 'Soạn đơn mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">✍️</span><h1 class="cat-title">Soạn Thảo Đơn Tố Tụng & Hành Chính Tự Động</h1>`;
        } else if (mode === 'auditor') {
            if (modeAuditorBtn) modeAuditorBtn.classList.add('active');
            if (viewAuditor) viewAuditor.classList.add('active');
            sidebarCategoriesSection.style.display = 'none';
            btnNewChatText.textContent = 'Thẩm tra mới';
            currentCategoryDisplay.innerHTML = `<span class="cat-icon">🛡️</span><h1 class="cat-title">Thẩm Tra Chứng Cứ & Khám Sức Khỏe Pháp Chế</h1>`;
        }
    }

    function handleNewSession() {
        if (currentMode === 'chat') {
            startNewChat();
        } else if (currentMode === 'review') {
            clearContractFile();
            contractManualText.value = '';
            reviewResultCard.style.display = 'none';
        } else if (currentMode === 'court') {
            resetCourtroom();
        } else if (currentMode === 'negotiate') {
            document.getElementById('negotiate-setup-card').style.display = 'block';
            document.getElementById('negotiate-arena').style.display = 'none';
        } else if (currentMode === 'petition') {
            document.getElementById('petition-form-card').style.display = 'flex';
            document.getElementById('petition-result-card').style.display = 'none';
        } else if (currentMode === 'auditor') {
            document.getElementById('evidence-result-card').style.display = 'none';
            document.getElementById('corp-result-card').style.display = 'none';
        }
    }

    // =========================================================================
    // MOOT COURT LOGIC (PHASE 3)
    // =========================================================================
    async function fetchCourtPresets() {
        try {
            const res = await fetch('/api/moot-court/presets');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    courtPresets = data;
                    renderCourtPresets();
                }
            }
        } catch (e) {
            console.warn('Lỗi lấy preset án tòa:', e);
        }
    }

    function renderCourtPresets() {
        presetCasesGrid.innerHTML = '';
        courtPresets.forEach((cs, idx) => {
            const card = document.createElement('div');
            card.className = `preset-case-card ${idx === 0 ? 'active' : ''}`;
            card.innerHTML = `
                <div class="case-card-header">
                    <span class="case-icon">${cs.icon}</span>
                    <div class="case-card-title">${cs.title}</div>
                </div>
                <div class="case-card-cat">${cs.category}</div>
            `;
            card.addEventListener('click', () => {
                document.querySelectorAll('.preset-case-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                selectPresetCase(cs);
            });
            presetCasesGrid.appendChild(card);
        });

        if (courtPresets.length > 0) {
            selectPresetCase(courtPresets[0]);
        }
    }

    function selectPresetCase(caseObj) {
        activeCourtCase = caseObj;
        customCaseTitle.value = caseObj.title;
        customCaseFacts.value = `${caseObj.facts}\n\nYêu cầu khởi kiện: ${caseObj.claim}`;
        customUserRole.value = caseObj.user_role;
    }

    function enterCourtArena() {
        const title = customCaseTitle.value.trim();
        const facts = customCaseFacts.value.trim();
        const role = customUserRole.value;

        if (!title || !facts) {
            alert('Vui lòng chọn một vụ án mẫu hoặc điền tóm tắt vụ việc của bạn.');
            return;
        }

        activeCourtCase = {
            title: title,
            facts: facts,
            user_role: role
        };

        arenaCaseTitle.textContent = title;
        arenaUserRole.textContent = `Tư cách của bạn: ${role}`;
        currentPersuasionScore = 50;
        updatePersuasionMeter(50);

        courtDialogueHistory = [];
        arenaTranscript.innerHTML = '';

        // Thẩm phán gõ búa khai mạc phiên tòa
        appendCourtBubble('judge', `🔨 [GÕ BÚA] TÒA ÁN NHÂN DÂN KHAI MẠC PHIÊN TÒA SƠ THẨM GIẢ LẬP.\n\n` +
            `Vụ việc xét xử: **${title}**.\n\n` +
            `Đề nghị các đương sự tuân thủ nghiêm ngặt nội quy phiên tòa theo Bộ luật Tố tụng Dân sự. ` +
            `Xin mời bên **${role}** bắt đầu trình bày yêu cầu khởi kiện và viện dẫn chứng cứ đầu tiên của mình!`);

        courtSetupCard.style.display = 'none';
        courtVerdictCard.style.display = 'none';
        courtArena.style.display = 'flex';
        arenaUserInput.focus();
    }

    async function sendCourtArgument() {
        const text = arenaUserInput.value.trim();
        if (!text) return;

        appendCourtBubble('user', text);
        courtDialogueHistory.push({ speaker: 'user', text: text });

        arenaUserInput.value = '';
        btnCourtSend.disabled = true;

        // Typing indicator cho luật sư đối tụng
        const typingRow = showCourtTypingIndicator();

        const apiKey = localStorage.getItem('ai_lawyer_api_key');
        const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

        try {
            const res = await fetch('/api/moot-court/turn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_title: activeCourtCase.title,
                    case_facts: activeCourtCase.facts,
                    user_role: activeCourtCase.user_role,
                    user_argument: text,
                    dialogue_history: courtDialogueHistory,
                    api_key: apiKey,
                    model: model
                })
            });

            typingRow.remove();
            btnCourtSend.disabled = false;

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(`⚠️ Lỗi: ${err.detail || 'Không thể kết nối tới phòng xử án.'}`);
                return;
            }

            const data = await res.json();
            appendCourtBubble('opposing', data.statement, data.tip);
            courtDialogueHistory.push({ speaker: 'opposing', text: data.statement });

            // Cập nhật điểm thuyết phục
            if (data.persuasion_score !== undefined) {
                updatePersuasionMeter(data.persuasion_score);
            }

        } catch (e) {
            typingRow.remove();
            btnCourtSend.disabled = false;
            alert('⚠️ Lỗi kết nối tới máy chủ đối chất.');
        }
    }

    async function requestCourtVerdict() {
        if (courtDialogueHistory.length < 2) {
            alert('Phiên tòa mới bắt đầu! Hãy đối chất ít nhất 1-2 lượt với Luật sư đối phương trước khi xin tuyên án.');
            return;
        }

        if (!confirm('Bạn có chắc muốn kết thúc tranh tụng và yêu cầu Thẩm phán ban hành Bản Án Sơ Bộ ngay không?')) {
            return;
        }

        btnRequestVerdict.disabled = true;
        btnRequestVerdict.textContent = '⏳ Đang nghị án...';

        const apiKey = localStorage.getItem('ai_lawyer_api_key');
        const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

        try {
            const res = await fetch('/api/moot-court/verdict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_title: activeCourtCase.title,
                    case_facts: activeCourtCase.facts,
                    user_role: activeCourtCase.user_role,
                    dialogue_history: courtDialogueHistory,
                    api_key: apiKey,
                    model: model
                })
            });

            btnRequestVerdict.disabled = false;
            btnRequestVerdict.innerHTML = '<span class="icon">⚖️</span><span>Tuyên Án Sơ Bộ</span>';

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                alert(`⚠️ Lỗi: ${err.detail || 'Không thể tạo bản án.'}`);
                return;
            }

            const data = await res.json();
            lastVerdictMarkdown = data.verdict_markdown;
            verdictContent.innerHTML = marked.parse(data.verdict_markdown);

            courtArena.style.display = 'none';
            courtVerdictCard.style.display = 'block';
            courtVerdictCard.scrollIntoView({ behavior: 'smooth' });

            saveSessionRecord(`[Phiên tòa] ${activeCourtCase.title}`);

        } catch (e) {
            btnRequestVerdict.disabled = false;
            btnRequestVerdict.innerHTML = '<span class="icon">⚖️</span><span>Tuyên Án Sơ Bộ</span>';
            alert('⚠️ Lỗi khi yêu cầu tuyên án.');
        }
    }

    async function downloadCourtVerdictDocx() {
        if (!lastVerdictMarkdown || !activeCourtCase) {
            alert('Chưa có nội dung bản án sơ bộ để xuất file Word.');
            return;
        }

        const btn = document.getElementById('btn-export-verdict-docx');
        const originalText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Đang tạo file Word...';
        }

        try {
            const response = await fetch('/api/moot-court/export-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_title: activeCourtCase.title,
                    user_role: activeCourtCase.user_role,
                    verdict_markdown: lastVerdictMarkdown,
                    dialogue_history: courtDialogueHistory
                })
            });

            if (!response.ok) throw new Error('Lỗi xuất Word bản án.');

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            const safeName = activeCourtCase.title.replace(/\s+/g, '_').substring(0, 30);
            a.download = `Ban_An_So_Bo_${safeName}.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (e) {
            alert('⚠️ Lỗi khi tải file Word bản án.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    }

    function appendCourtBubble(speaker, text, tip = null) {
        const row = document.createElement('div');
        row.className = `court-bubble-row ${speaker}`;

        const bubble = document.createElement('div');
        bubble.className = 'court-bubble';

        let speakerName = 'BẠN';
        let speakerIcon = '👤';
        if (speaker === 'opposing') {
            speakerName = 'LUẬT SƯ ĐỐI TỤNG (PHẢN BIỆN)';
            speakerIcon = '⚔️';
        } else if (speaker === 'judge') {
            speakerName = 'HỘI ĐỒNG XÉT XỬ (THẨM PHÁN)';
            speakerIcon = '⚖️';
        }

        let tipHtml = '';
        if (tip) {
            tipHtml = `<div class="court-tip-box">💡 <strong>Mách nước chiến thuật:</strong> ${tip}</div>`;
        }

        bubble.innerHTML = `
            <div class="court-bubble-speaker">${speakerIcon} ${speakerName}</div>
            <div class="court-bubble-text">${marked.parse(text)}</div>
            ${tipHtml}
        `;

        row.appendChild(bubble);
        arenaTranscript.appendChild(row);
        arenaTranscript.scrollTop = arenaTranscript.scrollHeight;
    }

    function showCourtTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'court-bubble-row opposing';
        row.innerHTML = `
            <div class="court-bubble">
                <div class="court-bubble-speaker">⚔️ LUẬT SƯ ĐỐI TỤNG</div>
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span style="margin-left: 8px; font-size: 12px; color: #F87171;">Đang soi lỗ hổng chứng cứ để phản bác...</span>
                </div>
            </div>
        `;
        arenaTranscript.appendChild(row);
        arenaTranscript.scrollTop = arenaTranscript.scrollHeight;
        return row;
    }

    function updatePersuasionMeter(score) {
        currentPersuasionScore = score;
        meterScoreText.textContent = `${score}%`;
        meterBarFill.style.width = `${score}%`;
        if (score >= 65) {
            meterScoreText.style.color = '#10B981';
        } else if (score >= 40) {
            meterScoreText.style.color = '#F59E0B';
        } else {
            meterScoreText.style.color = '#EF4444';
        }
    }

    function resetCourtroom() {
        courtArena.style.display = 'none';
        courtVerdictCard.style.display = 'none';
        courtSetupCard.style.display = 'flex';
    }

    // =========================================================================
    // CONTRACT REVIEW LOGIC (PHASE 2)
    // =========================================================================
    function setContractFile(file) {
        selectedContractFile = file;
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = formatBytes(file.size);
        dropzoneDefault.style.display = 'none';
        dropzoneSelected.style.display = 'flex';
    }

    function clearContractFile() {
        selectedContractFile = null;
        contractFileInput.value = '';
        chatFileInput.value = '';
        dropzoneDefault.style.display = 'block';
        dropzoneSelected.style.display = 'none';
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async function startContractReview() {
        const manualText = contractManualText.value.trim();

        if (!selectedContractFile && !manualText) {
            alert('Vui lòng kéo thả file hợp đồng (PDF, Word, TXT, Ảnh) hoặc dán điều khoản vào ô văn bản.');
            return;
        }

        reviewLoading.style.display = 'flex';
        reviewResultCard.style.display = 'none';
        btnStartReview.disabled = true;

        const formData = new FormData();
        if (selectedContractFile) formData.append('file', selectedContractFile);
        if (manualText) formData.append('text_content', manualText);
        formData.append('party_role', partyRoleSelect.value);
        if (focusAreasInput.value.trim()) formData.append('focus_areas', focusAreasInput.value.trim());

        const apiKey = localStorage.getItem('ai_lawyer_api_key');
        if (apiKey) formData.append('api_key', apiKey);

        const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';
        formData.append('model', model);

        try {
            const response = await fetch('/api/review-contract', {
                method: 'POST',
                body: formData
            });

            reviewLoading.style.display = 'none';
            btnStartReview.disabled = false;

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                alert(`⚠️ Lỗi: ${errData.detail || 'Không thể thực hiện thẩm định hợp đồng.'}`);
                return;
            }

            const data = await response.json();
            lastReviewRawText = data.review_result;
            lastReviewCitations = data.citations || [];

            resultDocName.textContent = `Báo Cáo Thẩm Định: ${data.filename || 'Dự thảo Hợp đồng'}`;
            if (resultModelBadge) resultModelBadge.textContent = '⚖️ Thẩm định hoàn tất';
            resultContent.innerHTML = marked.parse(data.review_result);
            reviewResultCard.style.display = 'block';
            reviewResultCard.scrollIntoView({ behavior: 'smooth' });

            saveSessionRecord(`[Thẩm định] ${data.filename || 'Hợp đồng'}`);

        } catch (error) {
            reviewLoading.style.display = 'none';
            btnStartReview.disabled = false;
            alert('⚠️ Lỗi kết nối tới máy chủ AI.');
        }
    }

    async function downloadContractDocx() {
        if (!lastReviewRawText) {
            alert('Chưa có nội dung kết quả thẩm định để xuất file Word.');
            return;
        }

        const originalHtml = btnExportDocx.innerHTML;
        btnExportDocx.disabled = true;
        btnExportDocx.innerHTML = '⏳ Đang tạo file Word...';

        try {
            const fileName = selectedContractFile ? selectedContractFile.name : 'Dự thảo Hợp đồng';
            const role = partyRoleSelect ? partyRoleSelect.value : 'Toàn diện';

            const response = await fetch('/api/export-contract-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    analysis_text: lastReviewRawText,
                    contract_title: fileName,
                    protect_side: role,
                    citations: lastReviewCitations
                })
            });

            if (!response.ok) throw new Error('Máy chủ phản hồi lỗi khi xuất Word.');

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            const safeName = fileName.replace(/\.[^/.]+$/, '').replace(/\s+/g, '_');
            a.download = `Bao_cao_tham_dinh_${safeName}.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);

            btnExportDocx.innerHTML = '✅ Đã tải file Word!';
            setTimeout(() => {
                btnExportDocx.innerHTML = originalHtml;
                btnExportDocx.disabled = false;
            }, 2500);

        } catch (err) {
            btnExportDocx.innerHTML = originalHtml;
            btnExportDocx.disabled = false;
            alert('Không thể tạo file Word. Vui lòng thử lại sau.');
        }
    }

    async function downloadChatDocx(topic, opinionText, citations = []) {
        try {
            const response = await fetch('/api/export-chat-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic || 'Tư vấn Pháp lý',
                    opinion_text: opinionText,
                    citations: citations
                })
            });

            if (!response.ok) throw new Error('Lỗi xuất file Word');

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            const safeTopic = (topic || 'AI_Lawyer').substring(0, 25).replace(/\s+/g, '_');
            a.download = `Thu_tu_van_phap_ly_${safeTopic}.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (e) {
            alert('Không thể xuất Thư tư vấn ra file Word. Vui lòng thử lại.');
        }
    }

    // =========================================================================
    // CHAT Q&A LOGIC (PHASE 1)
    // =========================================================================
    async function checkBackendHealth() {
        try {
            const res = await fetch('/api/health');
            if (res.ok) {
                const data = await res.json();
                const clientKey = localStorage.getItem('ai_lawyer_api_key');
                if (data.api_key_configured || clientKey) {
                    apiStatusDot.classList.add('active');
                    apiStatusDot.title = 'Hệ thống AI đã sẵn sàng';
                } else {
                    apiStatusDot.classList.remove('active');
                    apiStatusDot.title = 'Chưa cấu hình API Key';
                }
            }
        } catch (e) {
            apiStatusDot.classList.remove('active');
        }
    }

    async function fetchCategories() {
        try {
            const res = await fetch('/api/categories');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    categories = data;
                }
            }
        } catch (e) {
            console.warn('Lỗi tải danh mục:', e);
        }
        if (!Array.isArray(categories) || categories.length === 0) {
            categories = [{ id: 'all', name: 'Tư vấn Tổng hợp', icon: '⚖️', sample_questions: [] }];
        }
        renderCategories();
        renderQuickPrompts();
    }

    function renderCategories() {
        categoryListEl.innerHTML = '';
        categories.forEach(cat => {
            const item = document.createElement('div');
            item.className = `category-item ${cat.id === currentCategory.id ? 'active' : ''}`;
            item.innerHTML = `<span class="cat-icon">${cat.icon}</span><span>${cat.name}</span>`;
            item.addEventListener('click', () => {
                document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
                item.classList.add('active');
                currentCategory = cat;
                currentCategoryDisplay.innerHTML = `<span class="cat-icon">${cat.icon}</span><h1 class="cat-title">${cat.name}</h1>`;
                renderQuickPrompts();
            });
            categoryListEl.appendChild(item);
        });
    }

    function renderQuickPrompts() {
        quickPromptsGrid.innerHTML = '';
        const questions = currentCategory.sample_questions || (categories[0] ? categories[0].sample_questions : []);
        questions.forEach(q => {
            const card = document.createElement('div');
            card.className = 'prompt-card';
            card.textContent = q;
            card.addEventListener('click', () => {
                userInput.value = q;
                btnSend.disabled = false;
                sendMessage();
            });
            quickPromptsGrid.appendChild(card);
        });
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        welcomeScreen.style.display = 'none';
        appendMessage('user', text);
        userInput.value = '';
        btnSend.disabled = true;

        currentHistory.push({ role: 'user', content: text });
        const typingEl = showTypingIndicator();

        const apiKey = localStorage.getItem('ai_lawyer_api_key') || null;
        const model = localStorage.getItem('ai_lawyer_model') || 'gemini-3.5-flash';

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: currentHistory.slice(0, -1),
                    category: currentCategory.name,
                    api_key: apiKey,
                    model: model
                })
            });

            typingEl.remove();

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                appendMessage('assistant', `⚠️ **Lỗi:** ${errData.detail || 'Không thể kết nối máy chủ.'}`);
                return;
            }

            // Tạo message row cho assistant ngay lập tức để stream từng từ vào
            const row = document.createElement('div');
            row.className = 'message-row assistant';

            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = '⚖️';

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';

            // Khối chứa văn bản phản hồi được stream
            const textContainer = document.createElement('div');
            textContainer.className = 'message-stream-text';
            bubble.appendChild(textContainer);

            row.appendChild(avatar);
            row.appendChild(bubble);
            messagesList.appendChild(row);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Xử lý luồng SSE
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let accumulatedText = '';
            let streamCitations = [];
            let streamFollowUps = [];

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data:')) continue;
                    const jsonStr = trimmed.substring(5).trim();
                    if (!jsonStr) continue;

                    try {
                        const evt = JSON.parse(jsonStr);
                        if (evt.type === 'citations') {
                            streamCitations = evt.citations || [];
                            if (streamCitations.length > 0) {
                                renderCitationsInsideBubble(bubble, streamCitations, textContainer);
                            }
                        } else if (evt.type === 'token') {
                            accumulatedText += evt.token;
                            textContainer.innerHTML = marked.parse(accumulatedText);
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                        } else if (evt.type === 'follow_ups') {
                            streamFollowUps = evt.follow_ups || [];
                        } else if (evt.type === 'error') {
                            accumulatedText += `\n\n⚠️ **Lỗi:** ${evt.error}`;
                            textContainer.innerHTML = marked.parse(accumulatedText);
                        }
                    } catch (pe) {
                        console.error('Error parsing SSE event:', pe);
                    }
                }
            }

            // Render gợi ý hỏi tiếp (Follow-up chips)
            if (streamFollowUps.length > 0) {
                renderFollowUpsInsideBubble(bubble, streamFollowUps);
            }

            // Render thanh công cụ: Sao chép & Tải Word (.docx)
            renderMessageActions(bubble, text, accumulatedText, streamCitations);

            currentHistory.push({
                role: 'assistant',
                content: accumulatedText,
                citations: streamCitations,
                follow_ups: streamFollowUps
            });

            saveSessionRecord(text);
        } catch (error) {
            if (typingEl && typingEl.parentNode) typingEl.remove();
            appendMessage('assistant', `⚠️ **Lỗi kết nối tới máy chủ AI.** Vui lòng kiểm tra lại mạng hoặc thử lại.`);
        }
    }

    function appendMessage(role, content, citations = [], followUps = []) {
        const row = document.createElement('div');
        row.className = `message-row ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '⚖️';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        bubble.innerHTML = role === 'assistant' ? marked.parse(content) : escapeHtml(content);

        // 1. Render RAG Official Law Citations
        if (role === 'assistant' && citations && citations.length > 0) {
            renderCitationsInsideBubble(bubble, citations);
        }

        // 2. Render Interactive Socratic Follow-up Chips
        if (role === 'assistant' && followUps && followUps.length > 0) {
            renderFollowUpsInsideBubble(bubble, followUps);
        }

        // 3. Render Message Actions (Sao chép & Tải Word) cho trợ lý
        if (role === 'assistant' && !content.startsWith('⚠️ **Lỗi:')) {
            renderMessageActions(bubble, 'Tư vấn Pháp lý', content, citations);
        }

        if (role === 'user') {
            row.appendChild(bubble);
            row.appendChild(avatar);
        } else {
            row.appendChild(avatar);
            row.appendChild(bubble);
        }

        messagesList.appendChild(row);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return row;
    }

    function renderCitationsInsideBubble(bubble, citations, beforeElement = null) {
        if (!citations || citations.length === 0) return;
        const citeContainer = document.createElement('div');
        citeContainer.className = 'law-citations-container';
        citeContainer.innerHTML = `
            <div class="law-citations-title">📚 CĂN CỨ PHÁP LÝ ĐỐI CHIẾU CHÍNH QUY (VBPL.VN):</div>
            <div class="law-citations-list"></div>
        `;
        const citeList = citeContainer.querySelector('.law-citations-list');
        citations.forEach(c => {
            const badge = document.createElement('button');
            badge.className = 'law-citation-badge';
            badge.type = 'button';
            const artTitle = c.article_title || c.title || c.law_name || 'Điều luật';
            const artSrc = c.official_source || c.source || 'vbpl.vn';
            badge.title = `Nhấn để xem nguyên văn ${c.article_number} (${c.law_name})`;
            badge.innerHTML = `<span class="badge-icon">📖</span> <strong>${escapeHtml(c.article_number)}</strong>: ${escapeHtml(artTitle)} <span class="badge-source">${escapeHtml(artSrc)}</span>`;
            badge.addEventListener('click', () => {
                openLawModal(c);
            });
            citeList.appendChild(badge);
        });

        if (beforeElement && beforeElement.parentNode === bubble) {
            bubble.insertBefore(citeContainer, beforeElement);
        } else {
            bubble.appendChild(citeContainer);
        }
    }

    function renderFollowUpsInsideBubble(bubble, followUps) {
        if (!followUps || followUps.length === 0) return;
        const followUpContainer = document.createElement('div');
        followUpContainer.className = 'follow-ups-container';
        followUpContainer.innerHTML = `
            <div class="follow-ups-title">💡 GỢI Ý BƯỚC TIẾP THEO DÀNH CHO BẠN:</div>
            <div class="follow-ups-list"></div>
        `;
        const followUpList = followUpContainer.querySelector('.follow-ups-list');
        followUps.forEach(prompt => {
            const chip = document.createElement('button');
            chip.className = 'follow-up-chip';
            chip.type = 'button';
            chip.innerHTML = `<span class="chip-icon">💬</span> <span>${escapeHtml(prompt)}</span>`;
            chip.addEventListener('click', () => {
                userInput.value = prompt;
                userInput.style.height = 'auto';
                userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
                btnSend.disabled = false;
                sendMessage();
            });
            followUpList.appendChild(chip);
        });
        bubble.appendChild(followUpContainer);
    }

    function renderMessageActions(bubble, topic, opinionText, citations = []) {
        const actionsRow = document.createElement('div');
        actionsRow.className = 'chat-msg-actions';

        const btnCopy = document.createElement('button');
        btnCopy.type = 'button';
        btnCopy.className = 'btn-chat-action';
        btnCopy.innerHTML = '📋 Sao chép';
        btnCopy.title = 'Sao chép nội dung câu trả lời';
        btnCopy.addEventListener('click', () => {
            navigator.clipboard.writeText(opinionText);
            btnCopy.innerHTML = '✅ Đã sao chép!';
            setTimeout(() => btnCopy.innerHTML = '📋 Sao chép', 2000);
        });

        const btnDocx = document.createElement('button');
        btnDocx.type = 'button';
        btnDocx.className = 'btn-chat-action export-word';
        btnDocx.innerHTML = '📥 Tải Word (.docx)';
        btnDocx.title = 'Xuất ý kiến tư vấn pháp lý này ra file Word (.docx) chuyên nghiệp';
        btnDocx.addEventListener('click', () => {
            downloadChatDocx(topic, opinionText, citations);
        });

        actionsRow.appendChild(btnCopy);
        actionsRow.appendChild(btnDocx);
        bubble.appendChild(actionsRow);
    }

    function openLawModal(lawCitation) {
        const artNum = lawCitation.article_number || 'Điều luật';
        const artTitle = lawCitation.article_title || lawCitation.title || 'Nội dung điều luật';
        const lawName = lawCitation.law_name || 'Văn bản quy phạm pháp luật';
        const officialSrc = lawCitation.official_source || lawCitation.source || 'Cơ sở dữ liệu Quốc gia vbpl.vn';
        const fullContent = lawCitation.content || lawCitation.full_text || 'Đang cập nhật nội dung...';
        const officialUrl = lawCitation.official_source || lawCitation.url || 'https://vbpl.vn';

        lawModalTitle.textContent = `${artNum}: ${artTitle}`;
        lawModalSub.textContent = `Văn bản: ${lawName} • Nguồn: ${officialSrc}`;
        lawFullText.textContent = fullContent;
        lawOfficialLink.href = officialUrl.startsWith('http') ? officialUrl : 'https://vbpl.vn';
        lawModal.classList.add('open');
    }

    async function handleSidebarLawSearch() {
        const query = sidebarLawSearch.value.trim();
        if (!query) return;

        try {
            const res = await fetch(`/api/laws/search?q=${encodeURIComponent(query)}&limit=5`);
            if (!res.ok) {
                alert('Lỗi tra cứu văn bản pháp luật.');
                return;
            }
            const results = await res.json();
            if (results.length === 0) {
                alert(`Không tìm thấy điều luật phù hợp với từ khóa "${query}" trong CSDL Cổng Chính phủ.`);
                return;
            }

            const topResult = results[0];
            let combinedText = '';
            results.forEach((r, i) => {
                combinedText += `=== [ĐIỀU LUẬT ${i+1}/${results.length}] ${r.article_number}: ${r.title} ===\n(Thuộc: ${r.law_name})\nNguồn: ${r.source}\n\n${r.full_text}\n\n------------------------------------------------------------\n\n`;
            });

            lawModalTitle.textContent = `Tra cứu CSDL Chính phủ: "${query}" (${results.length} điều luật)`;
            lawModalSub.textContent = `Trích xuất từ Cơ sở dữ liệu Quốc gia về Văn bản Pháp luật (vbpl.vn)`;
            lawFullText.textContent = combinedText;
            lawOfficialLink.href = topResult.url || 'https://vbpl.vn';
            lawModal.classList.add('open');
        } catch (e) {
            alert('Lỗi kết nối máy chủ khi tra cứu văn bản pháp luật.');
        }
    }

    function showTypingIndicator() {
        const row = document.createElement('div');
        row.className = 'message-row assistant';
        row.innerHTML = `
            <div class="message-avatar">⚖️</div>
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span style="margin-left: 8px; font-size: 13px; color: var(--text-muted);">Luật sư AI đang nghiên cứu hồ sơ...</span>
                </div>
            </div>
        `;
        messagesList.appendChild(row);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return row;
    }

    function startNewChat() {
        currentSessionId = generateId();
        currentHistory = [];
        messagesList.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        renderQuickPrompts();
    }

    function saveSessionRecord(titleText) {
        const existingIdx = allSessions.findIndex(s => s.id === currentSessionId);
        const title = titleText.length > 38 ? titleText.substring(0, 38) + '...' : titleText;

        const sessionData = {
            id: currentSessionId,
            title: existingIdx >= 0 ? allSessions[existingIdx].title : title,
            category: currentCategory.name,
            messages: currentHistory,
            timestamp: new Date().toISOString()
        };

        if (existingIdx >= 0) allSessions[existingIdx] = sessionData;
        else allSessions.unshift(sessionData);

        if (allSessions.length > 30) allSessions.pop();
        localStorage.setItem('ai_lawyer_sessions', JSON.stringify(allSessions));
        renderHistory();
    }

    function loadSessions() {
        try {
            return JSON.parse(localStorage.getItem('ai_lawyer_sessions')) || [];
        } catch (e) { return []; }
    }

    function renderHistory() {
        if (allSessions.length === 0) {
            historyListEl.innerHTML = '<div class="history-empty">Chưa có phiên làm việc nào</div>';
            return;
        }

        historyListEl.innerHTML = '';
        allSessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `history-item ${session.id === currentSessionId ? 'active' : ''}`;
            item.textContent = session.title;
            item.addEventListener('click', () => {
                switchMode('chat');
                loadSession(session.id);
            });
            historyListEl.appendChild(item);
        });
    }

    function loadSession(id) {
        const session = allSessions.find(s => s.id === id);
        if (!session) return;

        currentSessionId = session.id;
        currentHistory = session.messages || [];
        welcomeScreen.style.display = 'none';
        messagesList.innerHTML = '';

        currentHistory.forEach(msg => appendMessage(msg.role, msg.content, msg.citations, msg.follow_ups));
        renderHistory();
    }

    function loadSavedSettings() {
        // Model silently defaults to gemini-2.5-flash
    }

    function updateModelBadge(modelName) {
        // Model name is hidden from user interface
    }

    function generateId() {
        return 'sess_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now();
    }

    // =========================================================================
    // WEB SPEECH-TO-TEXT VOICE INPUT
    // =========================================================================
    function initSpeechRecognition(buttonEl, targetInputEl) {
        if (!buttonEl || !targetInputEl) return;
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            buttonEl.title = 'Trình duyệt không hỗ trợ Web Speech API (Dùng Chrome/Edge)';
            buttonEl.addEventListener('click', () => {
                alert('Trình duyệt hiện tại không hỗ trợ Web Speech API. Bạn vui lòng sử dụng Google Chrome hoặc Microsoft Edge để nhập liệu bằng giọng nói.');
            });
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'vi-VN';
        recognition.continuous = false;
        recognition.interimResults = false;

        let isRecording = false;

        recognition.onstart = () => {
            isRecording = true;
            buttonEl.classList.add('recording');
            buttonEl.title = 'Đang lắng nghe tiếng Việt... Bạn hãy nói';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (transcript) {
                targetInputEl.value = (targetInputEl.value ? targetInputEl.value + ' ' : '') + transcript;
                targetInputEl.dispatchEvent(new Event('input'));
                targetInputEl.focus();
            }
        };

        recognition.onerror = (event) => {
            console.warn('Lỗi nhận diện giọng nói:', event.error);
            isRecording = false;
            buttonEl.classList.remove('recording');
        };

        recognition.onend = () => {
            isRecording = false;
            buttonEl.classList.remove('recording');
            buttonEl.title = 'Nhập liệu bằng giọng nói Tiếng Việt (Microphone)';
        };

        buttonEl.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (err) {
                    console.warn(err);
                }
            }
        });
    }

    // =========================================================================
    // LEGAL CALCULATOR MODAL
    // =========================================================================
    function initCalculatorModal() {
        if (!btnOpenCalc || !calcModal) return;

        btnOpenCalc.addEventListener('click', () => calcModal.classList.add('open'));
        if (btnCloseCalc) btnCloseCalc.addEventListener('click', () => calcModal.classList.remove('open'));
        calcModal.addEventListener('click', (e) => {
            if (e.target === calcModal) calcModal.classList.remove('open');
        });

        const calcTabs = document.querySelectorAll('.calc-tab-btn');
        const calcContents = document.querySelectorAll('.calc-tab-content');
        calcTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                calcTabs.forEach(t => t.classList.remove('active'));
                calcContents.forEach(c => c.style.display = 'none');
                tab.classList.add('active');
                const target = document.getElementById('tab-' + tab.getAttribute('data-tab'));
                if (target) target.style.display = 'block';
            });
        });

        const feeDisputeType = document.getElementById('calc-fee-dispute-type');
        const feeAmountGroup = document.getElementById('calc-fee-amount-group');
        if (feeDisputeType && feeAmountGroup) {
            feeDisputeType.addEventListener('change', () => {
                feeAmountGroup.style.display = feeDisputeType.value === 'non_monetary' ? 'none' : 'block';
            });
        }

        const btnDoCalcFee = document.getElementById('btn-do-calc-fee');
        const btnDoCalcInt = document.getElementById('btn-do-calc-int');
        const btnDoCalcTax = document.getElementById('btn-do-calc-tax');
        const btnDoCalcSev = document.getElementById('btn-do-calc-sev');

        if (btnDoCalcFee) {
            btnDoCalcFee.addEventListener('click', () => {
                const disputeType = document.getElementById('calc-fee-dispute-type').value;
                const hasValuation = disputeType !== 'non_monetary';
                const amount = parseFloat(document.getElementById('calc-fee-amount').value) || 0;
                executeCalculation({
                    calc_type: 'court_fee',
                    amount: amount,
                    dispute_type: disputeType,
                    has_valuation: hasValuation
                });
            });
        }

        if (btnDoCalcInt) {
            btnDoCalcInt.addEventListener('click', () => {
                const principal = parseFloat(document.getElementById('calc-int-principal').value) || 0;
                const rate = parseFloat(document.getElementById('calc-int-rate').value) || 10;
                const start = document.getElementById('calc-int-start').value;
                const end = document.getElementById('calc-int-end').value;
                if (!start || !end) {
                    alert('Vui lòng chọn ngày bắt đầu và ngày kết thúc.');
                    return;
                }
                executeCalculation({
                    calc_type: 'late_interest',
                    principal: principal,
                    rate_percent_per_year: rate,
                    start_date: start,
                    end_date: end
                });
            });
        }

        if (btnDoCalcTax) {
            btnDoCalcTax.addEventListener('click', () => {
                const price = parseFloat(document.getElementById('calc-tax-price').value) || 0;
                const isFirst = document.getElementById('calc-tax-first-home').checked;
                executeCalculation({
                    calc_type: 'property_tax',
                    price: price,
                    is_first_home: isFirst
                });
            });
        }

        if (btnDoCalcSev) {
            btnDoCalcSev.addEventListener('click', () => {
                const salary = parseFloat(document.getElementById('calc-sev-salary').value) || 0;
                const years = parseFloat(document.getElementById('calc-sev-years').value) || 0;
                executeCalculation({
                    calc_type: 'severance_allowance',
                    salary: salary,
                    working_years: years
                });
            });
        }
    }

    async function executeCalculation(payload) {
        const resultBox = document.getElementById('calc-result-box');
        const titleEl = document.getElementById('calc-result-title');
        const summaryEl = document.getElementById('calc-result-summary');
        const legalEl = document.getElementById('calc-result-legal');
        if (!resultBox) return;

        summaryEl.textContent = '⏳ Đang tính toán theo quy định pháp luật hiện hành...';
        resultBox.style.display = 'block';

        try {
            const res = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error('Lỗi tính toán');
            const data = await res.json();
            titleEl.textContent = data.title;
            summaryEl.innerHTML = `<strong>${data.summary_text}</strong>`;
            const detailsEl = document.getElementById('calc-result-details');
            if (detailsEl && data.result_details) {
                let detailsHtml = '<div style="margin-top: 10px; font-size: 13px; border-top: 1px dashed rgba(212,175,55,0.3); padding-top: 8px; display: flex; flex-direction: column; gap: 4px;">';
                if (data.result_details.court_fee !== undefined) {
                    detailsHtml += `<div>• Án phí sơ thẩm: <strong>${data.result_details.court_fee.toLocaleString('vi-VN')} VNĐ</strong></div>`;
                    detailsHtml += `<div>• Tạm ứng án phí nộp trước (50%): <strong style="color: #38BDF8;">${data.result_details.advance_fee.toLocaleString('vi-VN')} VNĐ</strong></div>`;
                }
                if (data.result_details.interest_amount !== undefined) {
                    detailsHtml += `<div>• Nợ gốc: <strong>${(data.result_details.principal || 0).toLocaleString('vi-VN')} VNĐ</strong></div>`;
                    detailsHtml += `<div>• Lãi phát sinh: <strong style="color: #F87171;">${data.result_details.interest_amount.toLocaleString('vi-VN')} VNĐ</strong> (${data.result_details.days_overdue} ngày)</div>`;
                    detailsHtml += `<div>• Tổng số tiền phải trả: <strong style="color: #4ADE80;">${(data.result_details.total_due || 0).toLocaleString('vi-VN')} VNĐ</strong></div>`;
                }
                if (data.result_details.total_tax !== undefined) {
                    if (data.result_details.is_first_home_exempt) {
                        detailsHtml += `<div style="color: #4ADE80;">• Miễn thuế TNCN 2% (nhà ở duy nhất)</div>`;
                    } else if (data.result_details.tax_tncn !== undefined) {
                        detailsHtml += `<div>• Thuế TNCN (2%): <strong>${data.result_details.tax_tncn.toLocaleString('vi-VN')} VNĐ</strong></div>`;
                    }
                    detailsHtml += `<div>• Lệ phí trước bạ (0.5%): <strong>${(data.result_details.fee_truoc_ba || 0).toLocaleString('vi-VN')} VNĐ</strong></div>`;
                    detailsHtml += `<div>• Tổng nghĩa vụ tài chính: <strong style="color: #F87171;">${(data.result_details.total_tax || 0).toLocaleString('vi-VN')} VNĐ</strong></div>`;
                }
                if (data.result_details.allowance_amount !== undefined) {
                    detailsHtml += `<div>• Tiền trợ cấp thôi việc: <strong style="color: #4ADE80;">${data.result_details.allowance_amount.toLocaleString('vi-VN')} VNĐ</strong></div>`;
                }
                detailsHtml += '</div>';
                detailsEl.innerHTML = detailsHtml;
            }
        } catch (e) {
            summaryEl.textContent = '⚠️ Đã xảy ra lỗi khi tính toán. Vui lòng kiểm tra lại số liệu nhập.';
        }
    }

    // =========================================================================
    // NEGOTIATION COACH
    // =========================================================================
    async function fetchNegotiatePresets() {
        if (negotiatePresets.length > 0) return;
        try {
            const res = await fetch('/api/negotiate/presets');
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    negotiatePresets = data;
                    renderNegotiatePresets();
                }
            }
        } catch (e) {
            console.warn('Lỗi lấy kịch bản đàm phán:', e);
        }
    }

    function renderNegotiatePresets() {
        const grid = document.getElementById('preset-negotiations-grid');
        if (!grid) return;
        grid.innerHTML = '';

        negotiatePresets.forEach((sc, idx) => {
            const card = document.createElement('div');
            card.className = `preset-neg-card ${idx === 0 ? 'active' : ''}`;
            card.innerHTML = `
                <div class="preset-neg-icon">${sc.icon}</div>
                <div class="preset-neg-title">${sc.title}</div>
                <div class="preset-neg-desc">${sc.context.substring(0, 85)}...</div>
            `;
            card.addEventListener('click', () => {
                document.querySelectorAll('.preset-neg-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                selectNegotiatePreset(sc);
            });
            grid.appendChild(card);
        });

        if (negotiatePresets.length > 0) selectNegotiatePreset(negotiatePresets[0]);
    }

    function selectNegotiatePreset(sc) {
        activeNegotiateScenario = sc;
        document.getElementById('custom-neg-title').value = sc.title;
        document.getElementById('custom-neg-user-role').value = sc.user_role;
        document.getElementById('custom-neg-opp-role').value = sc.opponent_role;
        document.getElementById('custom-neg-context').value = sc.context;
    }

    function startNegotiationSession() {
        const title = document.getElementById('custom-neg-title').value.trim();
        const uRole = document.getElementById('custom-neg-user-role').value.trim();
        const oRole = document.getElementById('custom-neg-opp-role').value.trim();
        const context = document.getElementById('custom-neg-context').value.trim();

        if (!title || !uRole || !oRole) {
            alert('Vui lòng điền đầy đủ chủ đề và vai trò của các bên thương lượng.');
            return;
        }

        activeNegotiateScenario = { title, user_role: uRole, opponent_role: oRole, context };
        document.getElementById('neg-arena-title').textContent = title;
        document.getElementById('neg-arena-roles').textContent = `Bạn: ${uRole} vs Đối phương: ${oRole}`;

        negotiateHistory = [];
        const transcriptEl = document.getElementById('neg-transcript');
        transcriptEl.innerHTML = '';
        updateNegotiateScore(50);

        appendNegotiateBubble('opponent', `Chào bạn! Tôi là **${oRole}**. Chúng ta ngồi lại đây để trao đổi rõ về vụ việc: "${title}". Bạn muốn đề xuất phương án giải quyết cụ thể như thế nào?`);

        document.getElementById('negotiate-setup-card').style.display = 'none';
        document.getElementById('negotiate-arena').style.display = 'flex';
        document.getElementById('neg-user-input').focus();
    }

    function updateNegotiateScore(score) {
        const scoreText = document.getElementById('neg-meter-score-text');
        const scoreBar = document.getElementById('neg-meter-bar-fill');
        if (scoreText) scoreText.textContent = `${score}%`;
        if (scoreBar) scoreBar.style.width = `${score}%`;
    }

    function appendNegotiateBubble(speaker, text, tacticalData = null) {
        const transcriptEl = document.getElementById('neg-transcript');
        const row = document.createElement('div');
        row.className = `court-bubble-row ${speaker === 'user' ? 'user' : 'opposing'}`;

        const bubble = document.createElement('div');
        bubble.className = 'court-bubble';

        const speakerName = speaker === 'user' ? 'BẠN (NGƯỜI THƯƠNG LƯỢNG)' : `ĐỐI PHƯƠNG (${activeNegotiateScenario ? activeNegotiateScenario.opponent_role : 'Đối tác'})`;
        const icon = speaker === 'user' ? '👤' : '🤝';

        let tacticalHtml = '';
        if (tacticalData) {
            tacticalHtml = `
                <div class="court-tip-box" style="margin-top: 10px; border-left-color: #D4AF37;">
                    <div style="font-weight:700; color: #D4AF37; margin-bottom: 4px;">⚖️ CỐ VẤN CHIẾN THUẬT HUỲNH NGUYÊN KHANG NHẬN XÉT:</div>
                    ${marked.parse(tacticalData)}
                </div>
            `;
        }

        bubble.innerHTML = `
            <div class="court-bubble-speaker">${icon} ${speakerName}</div>
            <div class="court-bubble-text">${marked.parse(text)}</div>
            ${tacticalHtml}
        `;

        row.appendChild(bubble);
        transcriptEl.appendChild(row);
        transcriptEl.scrollTop = transcriptEl.scrollHeight;
    }

    async function sendNegotiateTurn() {
        const inputEl = document.getElementById('neg-user-input');
        const text = inputEl.value.trim();
        if (!text) return;

        appendNegotiateBubble('user', text);
        negotiateHistory.push({ speaker: 'user', text: text });
        inputEl.value = '';

        const sendBtn = document.getElementById('btn-neg-send');
        sendBtn.disabled = true;

        const transcriptEl = document.getElementById('neg-transcript');
        const typingRow = document.createElement('div');
        typingRow.className = 'court-bubble-row opposing';
        typingRow.innerHTML = `
            <div class="court-bubble">
                <div class="court-bubble-speaker">🤝 ĐỐI PHƯƠNG</div>
                <div class="typing-indicator">
                    <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
                    <span style="margin-left: 8px; font-size: 12px; color: #94A3B8;">Đối tác đang cân nhắc và toan tính lợi ích...</span>
                </div>
            </div>
        `;
        transcriptEl.appendChild(typingRow);
        transcriptEl.scrollTop = transcriptEl.scrollHeight;

        try {
            const apiKey = localStorage.getItem('ai_lawyer_api_key');
            const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

            const res = await fetch('/api/negotiate/turn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario_title: activeNegotiateScenario.title,
                    user_role: activeNegotiateScenario.user_role,
                    opponent_role: activeNegotiateScenario.opponent_role,
                    context: activeNegotiateScenario.context,
                    user_message: text,
                    dialogue_history: negotiateHistory,
                    api_key: apiKey,
                    model: model
                })
            });

            transcriptEl.removeChild(typingRow);
            sendBtn.disabled = false;

            if (!res.ok) throw new Error('Lỗi đàm phán');
            const data = await res.json();

            appendNegotiateBubble('opponent', data.opponent_reply, data.tactical_analysis);
            negotiateHistory.push({ speaker: 'opponent', text: data.opponent_reply });

            updateNegotiateScore(data.deal_readiness_score);

            const tipBox = document.getElementById('neg-tip-box');
            const chipEl = document.getElementById('neg-recommended-chip');
            if (data.recommended_counter) {
                lastRecommendedCounter = data.recommended_counter;
                chipEl.textContent = `"${data.recommended_counter}"`;
                tipBox.style.display = 'block';
            } else {
                tipBox.style.display = 'none';
            }

            saveSessionRecord(`[Đàm phán] ${activeNegotiateScenario.title}`);

        } catch (e) {
            if (transcriptEl.contains(typingRow)) transcriptEl.removeChild(typingRow);
            sendBtn.disabled = false;
            alert('⚠️ Lỗi khi gửi lời đàm phán.');
        }
    }

    // =========================================================================
    // PETITION GENERATOR
    // =========================================================================
    function initPetitionGenerator() {
        const btnGen = document.getElementById('btn-generate-petition');
        if (btnGen) btnGen.addEventListener('click', generatePetitionAction);

        const btnExportDoc = document.getElementById('btn-export-petition-docx');
        if (btnExportDoc) btnExportDoc.addEventListener('click', downloadPetitionDocx);

        const btnEdit = document.getElementById('btn-edit-petition');
        if (btnEdit) {
            btnEdit.addEventListener('click', () => {
                document.getElementById('petition-result-card').style.display = 'none';
                document.getElementById('petition-form-card').style.display = 'flex';
                document.getElementById('petition-form-card').scrollIntoView({ behavior: 'smooth' });
            });
        }

        const btnCopy = document.getElementById('btn-copy-petition');
        if (btnCopy) {
            btnCopy.addEventListener('click', () => {
                if (lastPetitionMarkdown) {
                    navigator.clipboard.writeText(lastPetitionMarkdown);
                    btnCopy.textContent = '✅ Đã sao chép!';
                    setTimeout(() => btnCopy.textContent = '📋 Sao chép', 2000);
                }
            });
        }
    }

    async function generatePetitionAction() {
        const pType = document.getElementById('petition-type-select').value;
        const pName = document.getElementById('pet-plaintiff-name').value.trim();
        const pId = document.getElementById('pet-plaintiff-id').value.trim();
        const pPhone = document.getElementById('pet-plaintiff-phone').value.trim();
        const pAddr = document.getElementById('pet-plaintiff-address').value.trim();

        const dName = document.getElementById('pet-defendant-name').value.trim();
        const dPhone = document.getElementById('pet-defendant-phone').value.trim();
        const dAddr = document.getElementById('pet-defendant-address').value.trim();

        const facts = document.getElementById('pet-facts').value.trim();
        const claims = document.getElementById('pet-claims').value.trim();
        const evidence = document.getElementById('pet-evidence').value.trim();

        if (!pName || !facts || !claims) {
            alert('Vui lòng điền Họ tên người làm đơn, tóm tắt sự việc và nội dung yêu cầu giải quyết.');
            return;
        }

        const loading = document.getElementById('petition-loading');
        const formCard = document.getElementById('petition-form-card');
        const resultCard = document.getElementById('petition-result-card');

        loading.style.display = 'flex';
        formCard.style.display = 'none';
        resultCard.style.display = 'none';

        try {
            const apiKey = localStorage.getItem('ai_lawyer_api_key');
            const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

            const res = await fetch('/api/petitions/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    petition_type: pType,
                    plaintiff_info: { name: pName, id_number: pId, phone: pPhone, address: pAddr },
                    defendant_info: { name: dName, phone: dPhone, address: dAddr },
                    facts: facts,
                    claims: claims,
                    evidence_list: evidence,
                    api_key: apiKey,
                    model: model
                })
            });

            loading.style.display = 'none';

            if (!res.ok) {
                formCard.style.display = 'flex';
                throw new Error('Không thể tạo đơn');
            }

            const data = await res.json();
            lastPetitionMarkdown = data.content_markdown;
            lastPetitionTitle = data.petition_title;

            document.getElementById('pet-result-title').textContent = data.petition_title;
            document.getElementById('pet-result-content').innerHTML = marked.parse(data.content_markdown);

            resultCard.style.display = 'block';
            resultCard.scrollIntoView({ behavior: 'smooth' });

            saveSessionRecord(`[Đơn từ] ${data.petition_title}`);

        } catch (e) {
            loading.style.display = 'none';
            formCard.style.display = 'flex';
            alert('⚠️ Lỗi khi soạn thảo đơn từ. Vui lòng thử lại.');
        }
    }

    async function downloadPetitionDocx() {
        if (!lastPetitionMarkdown) return;
        const btn = document.getElementById('btn-export-petition-docx');
        const oldText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Đang tạo file Word...';
        }

        try {
            const res = await fetch('/api/petitions/export-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    petition_title: lastPetitionTitle || 'ĐƠN TỐ TỤNG',
                    content_markdown: lastPetitionMarkdown
                })
            });
            if (!res.ok) throw new Error('Lỗi xuất Word');
            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `${(lastPetitionTitle || 'Don_to_tung').replace(/\s+/g, '_')}.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (e) {
            alert('⚠️ Không thể tải file Word đơn từ.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = oldText;
            }
        }
    }

    // =========================================================================
    // AUDITOR: EVIDENCE STRENGTH & CORPORATE COMPLIANCE
    // =========================================================================
    function initAuditor() {
        const tabEv = document.getElementById('tab-evidence-audit');
        const tabCorp = document.getElementById('tab-corporate-audit');
        const panelEv = document.getElementById('subpanel-evidence');
        const panelCorp = document.getElementById('subpanel-corporate');

        if (tabEv && tabCorp) {
            tabEv.addEventListener('click', () => {
                tabEv.classList.add('active');
                tabCorp.classList.remove('active');
                panelEv.style.display = 'block';
                panelCorp.style.display = 'none';
            });
            tabCorp.addEventListener('click', () => {
                tabCorp.classList.add('active');
                tabEv.classList.remove('active');
                panelCorp.style.display = 'block';
                panelEv.style.display = 'none';
            });
        }

        const btnAddRow = document.getElementById('btn-add-evidence-row');
        if (btnAddRow) {
            btnAddRow.addEventListener('click', () => {
                const rowsContainer = document.getElementById('evidence-input-rows');
                const count = rowsContainer.querySelectorAll('.evidence-row-input').length + 1;
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'evidence-row-input';
                input.placeholder = `Chứng cứ ${count}: Nhập tên tài liệu / ghi âm / vi bằng...`;
                rowsContainer.appendChild(input);
                input.focus();
            });
        }

        const btnStartEv = document.getElementById('btn-start-evidence-audit');
        if (btnStartEv) btnStartEv.addEventListener('click', executeEvidenceAudit);

        const btnStartCorp = document.getElementById('btn-start-corp-audit');
        if (btnStartCorp) btnStartCorp.addEventListener('click', executeCorporateAudit);

        const btnExportCorp = document.getElementById('btn-export-corp-docx');
        if (btnExportCorp) btnExportCorp.addEventListener('click', downloadCorporateDocx);
    }

    async function executeEvidenceAudit() {
        const summary = document.getElementById('ev-case-summary').value.trim();
        const inputs = document.querySelectorAll('.evidence-row-input');
        const items = [];
        inputs.forEach(inp => {
            const val = inp.value.trim();
            if (val) items.push(val);
        });

        if (!summary || items.length === 0) {
            alert('Vui lòng nhập tóm tắt vụ việc và ít nhất một tài liệu chứng cứ cần thẩm tra.');
            return;
        }

        const loading = document.getElementById('evidence-loading');
        const resultCard = document.getElementById('evidence-result-card');
        loading.style.display = 'flex';
        resultCard.style.display = 'none';

        try {
            const apiKey = localStorage.getItem('ai_lawyer_api_key');
            const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

            const res = await fetch('/api/evidence/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_summary: summary,
                    evidence_items: items,
                    api_key: apiKey,
                    model: model
                })
            });

            loading.style.display = 'none';
            if (!res.ok) throw new Error('Lỗi thẩm tra chứng cứ');

            const data = await res.json();
            document.getElementById('ev-overall-badge').textContent = `Độ vững chắc: ${data.overall_strength} (Điểm bình quân: ${data.average_grade})`;

            const tbody = document.getElementById('evidence-table-body');
            tbody.innerHTML = '';

            data.items.forEach(it => {
                const tr = document.createElement('tr');
                const gradeClass = 'grade-' + it.grade.replace('+', '-plus');
                tr.innerHTML = `
                    <td><strong>${escapeHtml(it.item)}</strong></td>
                    <td style="text-align: center;"><span class="grade-badge ${gradeClass}">${it.grade}</span></td>
                    <td>${escapeHtml(it.probative_value)}</td>
                    <td style="color: #F87171;">${escapeHtml(it.vulnerability)}</td>
                    <td style="color: #38BDF8;">💡 ${escapeHtml(it.remedy)}</td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('ev-general-recommendations').innerHTML = marked.parse(data.general_recommendations);
            resultCard.style.display = 'block';
            resultCard.scrollIntoView({ behavior: 'smooth' });

            saveSessionRecord(`[Thẩm tra chứng cứ] ${summary.substring(0, 30)}`);

        } catch (e) {
            loading.style.display = 'none';
            alert('⚠️ Lỗi thẩm tra chứng cứ. Vui lòng thử lại.');
        }
    }

    async function executeCorporateAudit() {
        const cName = document.getElementById('corp-name').value.trim();
        const cType = document.getElementById('corp-type').value;
        const cCount = parseInt(document.getElementById('corp-emp-count').value) || 10;
        const cIndustry = document.getElementById('corp-industry').value.trim();
        const cNotes = document.getElementById('corp-notes').value.trim();

        if (!cName || !cIndustry) {
            alert('Vui lòng nhập tên công ty và ngành nghề kinh doanh chính.');
            return;
        }

        const loading = document.getElementById('corp-loading');
        const resultCard = document.getElementById('corp-result-card');
        loading.style.display = 'flex';
        resultCard.style.display = 'none';

        try {
            const apiKey = localStorage.getItem('ai_lawyer_api_key');
            const model = localStorage.getItem('ai_lawyer_model') || 'gemini-2.5-flash';

            const res = await fetch('/api/corporate/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: cName,
                    business_type: cType,
                    employee_count: cCount,
                    industry: cIndustry,
                    compliance_notes: cNotes,
                    api_key: apiKey,
                    model: model
                })
            });

            loading.style.display = 'none';
            if (!res.ok) throw new Error('Lỗi khám sức khỏe pháp chế');

            const data = await res.json();
            lastCorporateData = data;
            lastCorporateData.business_type = cType;
            lastCorporateData.industry = cIndustry;

            document.getElementById('corp-result-company').textContent = `Báo Cáo Pháp Chế: ${data.company_name}`;
            document.getElementById('corp-score-badge').textContent = `Điểm tuân thủ: ${data.compliance_score}/100`;
            document.getElementById('corp-summary-text').innerHTML = `<strong>Đánh giá chung:</strong> ${data.summary}`;

            const grid = document.getElementById('corp-pillars-grid');
            grid.innerHTML = '';

            data.pillars.forEach(p => {
                const card = document.createElement('div');
                card.className = `pillar-card status-${p.status}`;
                const badgeLabel = p.status === 'compliant' ? 'ĐẠT' : (p.status === 'warning' ? 'CẢNH BÁO' : 'NGHIÊM TRỌNG');
                card.innerHTML = `
                    <div class="pillar-title">
                        <span>${p.pillar_name}</span>
                        <span class="pillar-badge ${p.status}">${badgeLabel}</span>
                    </div>
                    <div class="pillar-risk"><strong>Rủi ro:</strong> ${p.risk_summary}</div>
                    <div class="pillar-remedy"><strong>Khắc phục:</strong> ${p.remediation_action}</div>
                    <div style="font-size: 11px; color: #64748B; margin-top: 4px;">📜 ${p.legal_basis}</div>
                `;
                grid.appendChild(card);
            });

            resultCard.style.display = 'block';
            resultCard.scrollIntoView({ behavior: 'smooth' });

            saveSessionRecord(`[Pháp chế DN] ${cName}`);

        } catch (e) {
            loading.style.display = 'none';
            alert('⚠️ Lỗi khám sức khỏe pháp chế doanh nghiệp.');
        }
    }

    async function downloadCorporateDocx() {
        if (!lastCorporateData) return;
        const btn = document.getElementById('btn-export-corp-docx');
        const oldText = btn ? btn.innerHTML : '';
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '⏳ Đang tạo file Word...';
        }

        try {
            const res = await fetch('/api/corporate/export-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: lastCorporateData.company_name,
                    business_type: lastCorporateData.business_type || 'Doanh nghiệp',
                    industry: lastCorporateData.industry || 'Kinh doanh',
                    compliance_score: lastCorporateData.compliance_score,
                    summary: lastCorporateData.summary,
                    pillars: lastCorporateData.pillars
                })
            });

            if (!res.ok) throw new Error('Lỗi xuất Word');
            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `Bao_Cao_Phap_Che_${lastCorporateData.company_name.replace(/\s+/g, '_')}.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (e) {
            alert('⚠️ Không thể tải file Word báo cáo pháp chế.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = oldText;
            }
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
