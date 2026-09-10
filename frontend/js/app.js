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
    const viewChat = document.getElementById('view-chat');
    const viewReview = document.getElementById('view-review');
    const viewCourt = document.getElementById('view-court');
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

    // --- DOM Elements: Settings Modal ---
    const btnOpenSettings = document.getElementById('btn-open-settings');
    const settingsModal = document.getElementById('settings-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
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
    let currentMode = 'chat'; // 'chat' | 'review' | 'court'
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

        // 3 Navigation Modes
        modeChatBtn.addEventListener('click', () => switchMode('chat'));
        modeReviewBtn.addEventListener('click', () => switchMode('review'));
        modeCourtBtn.addEventListener('click', () => switchMode('court'));

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

        btnCloseModal.addEventListener('click', () => settingsModal.classList.remove('open'));
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

    // --- Mode Switching (Chat vs Review vs Court) ---
    function switchMode(mode) {
        currentMode = mode;
        [modeChatBtn, modeReviewBtn, modeCourtBtn].forEach(b => b.classList.remove('active'));
        [viewChat, viewReview, viewCourt].forEach(v => v.classList.remove('active'));

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
        }
    }

    // =========================================================================
    // MOOT COURT LOGIC (PHASE 3)
    // =========================================================================
    async function fetchCourtPresets() {
        try {
            const res = await fetch('/api/moot-court/presets');
            if (res.ok) {
                courtPresets = await res.json();
                renderCourtPresets();
            }
        } catch (e) {
            console.warn('Lỗi lấy preset án tòa');
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
            if (res.ok) categories = await res.json();
        } catch (e) {
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

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
