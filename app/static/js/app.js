// Chat-with-Love 前端交互引擎
document.addEventListener('DOMContentLoaded', () => {
  // 状态变量
  let currentImageFile = null;
  let currentImageBase64 = null;

  // DOM 元素
  const tabPasteImg = document.getElementById('tabPasteImg');
  const tabPasteText = document.getElementById('tabPasteText');
  const viewPasteImg = document.getElementById('viewPasteImg');
  const viewPasteText = document.getElementById('viewPasteText');

  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const dropPrompt = document.getElementById('dropPrompt');
  const imagePreviewContainer = document.getElementById('imagePreviewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const btnRemoveImage = document.getElementById('btnRemoveImage');
  const btnAnalyzeImage = document.getElementById('btnAnalyzeImage');

  const inputText = document.getElementById('inputText');
  const btnAnalyzeText = document.getElementById('btnAnalyzeText');
  const inputAlias = document.getElementById('inputAlias');
  const inputUserMbti = document.getElementById('inputUserMbti');
  const inputTargetMbti = document.getElementById('inputTargetMbti');

  const bubbleList = document.getElementById('bubbleList');
  const dialogueCount = document.getElementById('dialogueCount');

  const valStrategy = document.getElementById('valStrategy');
  const valStrategyDesc = document.getElementById('valStrategyDesc');
  const valIntent = document.getElementById('valIntent');
  const valEmotion = document.getElementById('valEmotion');
  const valShitTest = document.getElementById('valShitTest');
  const valShitTestProb = document.getElementById('valShitTestProb');

  const numInterest = document.getElementById('numInterest');
  const barInterest = document.getElementById('barInterest');
  const numDefense = document.getElementById('numDefense');
  const barDefense = document.getElementById('barDefense');
  const numPower = document.getElementById('numPower');
  const barPower = document.getElementById('barPower');
  const latencyBadge = document.getElementById('latencyBadge');

  const replyList = document.getElementById('replyList');
  const branchCard = document.getElementById('branchCard');
  const branchPos = document.getElementById('branchPos');
  const branchNeu = document.getElementById('branchNeu');
  const branchNeg = document.getElementById('branchNeg');

  // 配置弹窗
  const btnSettings = document.getElementById('btnSettings');
  const modalConfig = document.getElementById('modalConfig');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');
  const btnSaveConfig = document.getElementById('btnSaveConfig');
  const cfgJevKey = document.getElementById('cfgJevKey');
  const cfgJevUrl = document.getElementById('cfgJevUrl');
  const cfgLlmKey = document.getElementById('cfgLlmKey');
  const cfgLlmUrl = document.getElementById('cfgLlmUrl');
  const cfgLlmModel = document.getElementById('cfgLlmModel');

  // 1. 标签切换
  tabPasteImg.addEventListener('click', () => {
    tabPasteImg.classList.add('text-pink-600', 'border-b-2', 'border-pink-500');
    tabPasteImg.classList.remove('text-slate-400');
    tabPasteText.classList.remove('text-pink-600', 'border-b-2', 'border-pink-500');
    tabPasteText.classList.add('text-slate-400');
    viewPasteImg.classList.remove('hidden');
    viewPasteText.classList.add('hidden');
  });

  tabPasteText.addEventListener('click', () => {
    tabPasteText.classList.add('text-pink-600', 'border-b-2', 'border-pink-500');
    tabPasteText.classList.remove('text-slate-400');
    tabPasteImg.classList.remove('text-pink-600', 'border-b-2', 'border-pink-500');
    tabPasteImg.classList.add('text-slate-400');
    viewPasteText.classList.remove('hidden');
    viewPasteImg.classList.add('hidden');
  });

  // 2. 剪贴板一键粘贴 (Ctrl+V / Cmd+V)
  window.addEventListener('paste', (e) => {
    // 如果在文本框内粘贴文字，不拦截图片逻辑
    if (document.activeElement === inputText) return;

    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        handleImageSelection(file);
        // 自动切回图片标签
        tabPasteImg.click();
        e.preventDefault();
        break;
      }
    }
  });

  // 点击选择文件
  dropZone.addEventListener('click', () => {
    if (!currentImageFile) fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageSelection(e.target.files[0]);
    }
  });

  // 拖拽上传
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-pink-500', 'bg-pink-100/50');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-pink-500', 'bg-pink-100/50');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-pink-500', 'bg-pink-100/50');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageSelection(e.dataTransfer.files[0]);
    }
  });

  function handleImageSelection(file) {
    if (!file || !file.type.startsWith('image/')) return;
    currentImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      currentImageBase64 = e.target.result;
      imagePreview.src = currentImageBase64;
      dropPrompt.classList.add('hidden');
      imagePreviewContainer.classList.remove('hidden');
      btnAnalyzeImage.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  btnRemoveImage.addEventListener('click', (e) => {
    e.stopPropagation();
    currentImageFile = null;
    currentImageBase64 = null;
    fileInput.value = '';
    imagePreview.src = '';
    imagePreviewContainer.classList.add('hidden');
    dropPrompt.classList.remove('hidden');
    btnAnalyzeImage.disabled = true;
  });

  // 3. 实战案例快速载入
  const demoCases = {
    tired: `我: 今天工作顺利吗？\n对方: 别提了，连轴转开了一整天会，整个人都快散架了😭\n对方: 现在刚回到家，动都不想动`,
    cold: `我: 周末这家餐厅看起来不错，一起去尝尝吗？\n对方: 哦\n对方: 随便吧`,
    shittest: `对方: 你平时是不是对所有女生都这么会说话啊？\n对方: 感觉你很像海王哎😏`
  };

  document.querySelectorAll('.btnDemo').forEach(btn => {
    btn.addEventListener('click', () => {
      const caseKey = btn.getAttribute('data-case');
      inputText.value = demoCases[caseKey] || '';
    });
  });

  // 4. 分析请求执行 (SSE 流式打字机 0.2 秒极速反馈)
  btnAnalyzeText.addEventListener('click', () => {
    const text = inputText.value.trim();
    if (!text) {
      alert('请先输入或粘贴聊天文字记录');
      return;
    }
    executeAnalysisStream({
      text: text,
      target_alias: inputAlias.value.trim() || '对方',
      user_mbti: inputUserMbti.value.trim(),
      target_mbti: inputTargetMbti.value.trim()
    });
  });

  btnAnalyzeImage.addEventListener('click', () => {
    if (!currentImageBase64) return;
    executeAnalysisStream({
      image_base64: currentImageBase64,
      target_alias: inputAlias.value.trim() || '对方',
      user_mbti: inputUserMbti.value.trim(),
      target_mbti: inputTargetMbti.value.trim()
    });
  });

  function resetForNewAnalysis() {
    latencyBadge.textContent = '⚡ 0.0s 引擎启动中...';
    valStrategy.innerHTML = '<span class="text-pink-400 animate-pulse">判决中...</span>';
    valStrategyDesc.textContent = '正在识别互动动因与权力位态';
    valIntent.innerHTML = '<span class="text-slate-400 animate-pulse">动机分析中...</span>';
    valEmotion.textContent = '情绪状态：--';
    valShitTest.innerHTML = '<span class="text-slate-400">检测中...</span>';
    valShitTestProb.textContent = '置信概率：--';
    
    numInterest.textContent = '--';
    barInterest.style.width = '0%';
    numDefense.textContent = '--';
    barDefense.style.width = '0%';
    numPower.textContent = '--';
    barPower.style.width = '0%';
    
    branchCard.classList.add('hidden');
    replyList.innerHTML = `
      <div class="text-center py-12 text-slate-400 text-xs flex flex-col items-center gap-2">
        <span class="animate-spin text-lg">✨</span>
        <span>Jev 系统一正在 0.2 秒极速心智判决，即将流式呈现三阶实战回复...</span>
      </div>
    `;
  }

  function initStreamReplyCards() {
    replyList.innerHTML = '';
    const tiers = [
      { name: '稳健走心版', style: { badgeBg: 'bg-emerald-100 text-emerald-800', border: 'border-emerald-200' } },
      { name: '高情商策略版', style: { badgeBg: 'bg-pink-100 text-pink-800', border: 'border-pink-200' } },
      { name: '设立边界版', style: { badgeBg: 'bg-purple-100 text-purple-800', border: 'border-purple-200' } }
    ];

    tiers.forEach((t, idx) => {
      const card = document.createElement('div');
      card.id = `stream-card-${idx}`;
      card.setAttribute('data-tier', t.name);
      card.className = `p-4 rounded-xl border ${t.style.border} bg-white shadow-xs flex flex-col space-y-2 relative transition-all duration-300`;

      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-xs font-bold ${t.style.badgeBg}">${t.name}</span>
            <span class="card-timing text-[11px] text-slate-400">⏰ 适时发送</span>
          </div>
          <span class="status-indicator text-[11px] text-pink-500 font-medium flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-pink-500 animate-ping"></span>
            <span>军师打字中...</span>
          </span>
        </div>
        <div class="card-content text-xs text-slate-800 font-medium bg-slate-50/80 p-2.5 rounded-lg border border-slate-100 min-h-[46px] leading-relaxed">
          <span class="typing-cursor"></span>
        </div>
        <p class="card-rationale text-[11px] text-slate-500 leading-normal flex items-start gap-1">
          <span class="text-pink-500 font-bold shrink-0">💡 心理学设计：</span>
          <span class="rationale-text text-slate-400">正在分析心智动因...</span>
        </p>
      `;
      replyList.appendChild(card);
    });
  }

  function updateStreamReplyCards(replies, branch) {
    if (!replies || replies.length === 0) return;

    replies.forEach(rep => {
      const card = replyList.querySelector(`[data-tier="${rep.tier}"]`);
      if (!card) return;

      const contentEl = card.querySelector('.card-content');
      const rationaleEl = card.querySelector('.rationale-text');
      const timingEl = card.querySelector('.card-timing');

      if (rep.content && contentEl) {
        contentEl.innerHTML = escapeHtml(rep.content) + '<span class="typing-cursor"></span>';
      }
      if (rep.rationale && rationaleEl) {
        rationaleEl.textContent = rep.rationale;
        rationaleEl.classList.remove('text-slate-400');
        rationaleEl.classList.add('text-slate-600');
      }
      if (rep.timing && timingEl) {
        timingEl.textContent = '⏰ ' + rep.timing;
      }
    });

    if (branch && (branch.if_positive || branch.if_neutral || branch.if_cooling)) {
      branchCard.classList.remove('hidden');
      if (branch.if_positive) branchPos.textContent = branch.if_positive;
      if (branch.if_neutral) branchNeu.textContent = branch.if_neutral;
      if (branch.if_cooling) branchNeg.textContent = branch.if_cooling;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }

  async function executeAnalysisStream(payload) {
    setLoading(true);
    resetForNewAnalysis();

    try {
      const response = await fetch('/api/analyze/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`服务响应异常 HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let jevReceived = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // 保留不完整的一行

        let currentEvent = null;
        for (let line of lines) {
          line = line.trim();
          if (!line) continue;

          if (line.startsWith('event: ')) {
            currentEvent = line.substring(7).trim();
          } else if (line.startsWith('data: ')) {
            const dataStr = line.substring(6).trim();
            try {
              const data = JSON.parse(dataStr);

              if (currentEvent === 'dialogue') {
                renderBubbles(data.dialogue);
                dialogueCount.textContent = `共还原 ${data.dialogue.length} 条 (离线OCR本地极速解析)`;
                latencyBadge.textContent = `⚡ 离线OCR解析 (${data.latency_ms} ms)`;
              } else if (currentEvent === 'jev') {
                jevReceived = true;
                const jev = data.jev;
                latencyBadge.textContent = `⚡ 0.2s 极速决策完成 (Jev系统一耗时 ${data.latency_ms} ms)`;

                valStrategy.innerHTML = `<span class="text-pink-600 font-bold">${jev.primary_strategy}</span>`;
                valStrategyDesc.textContent = jev.strategy_explanation || '';
                valIntent.innerHTML = `<span>${jev.hidden_intent}</span>`;
                valEmotion.textContent = `情绪状态：${jev.emotional_state || '平稳'}`;

                if (jev.is_shit_test) {
                  valShitTest.innerHTML = `<span class="text-amber-600 font-bold">检测到测试 ⚠️</span>`;
                  valShitTestProb.textContent = `置信度: ${(jev.shit_test_prob * 100).toFixed(0)}% (建议化解反撩)`;
                } else {
                  valShitTest.innerHTML = `<span class="text-emerald-600 font-bold">正常交流 ✅</span>`;
                  valShitTestProb.textContent = `置信度: ${(jev.shit_test_prob * 100).toFixed(0)}% (无设防陷阱)`;
                }

                // 三维心理雷达滑竿动画
                numInterest.textContent = `${jev.interest_score}分`;
                barInterest.style.width = `${jev.interest_score}%`;

                numDefense.textContent = `${jev.defense_score}分`;
                barDefense.style.width = `${jev.defense_score}%`;

                numPower.textContent = `${jev.power_dynamic}%`;
                barPower.style.width = `${jev.power_dynamic}%`;

                // 立即点亮三阶话术卡片打字机骨架
                initStreamReplyCards();

              } else if (currentEvent === 'stream_delta') {
                if (!jevReceived) {
                  initStreamReplyCards();
                  jevReceived = true;
                }
                updateStreamReplyCards(data.replies, data.branch);

              } else if (currentEvent === 'done') {
                renderAnalysisResult(data);

              } else if (currentEvent === 'error') {
                alert('分析提示: ' + (data.error || '未知异常'));
              }
            } catch (err) {
              console.error('SSE JSON 解析错误:', err, dataStr);
            }
          }
        }
      }
    } catch (err) {
      alert('分析请求失败: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    btnAnalyzeText.disabled = isLoading;
    btnAnalyzeImage.disabled = isLoading;
    if (isLoading) {
      btnAnalyzeText.innerHTML = `<span class="animate-spin mr-2">⏳</span> 正在极速解码与打字流式输出...`;
      btnAnalyzeImage.innerHTML = `<span class="animate-spin mr-2">⏳</span> 正在极速解码与打字流式输出...`;
    } else {
      btnAnalyzeText.innerHTML = `<i data-lucide="sparkle" class="w-4 h-4"></i><span>启动军师分析 (Jev心智解码)</span>`;
      btnAnalyzeImage.innerHTML = `<i data-lucide="sparkle" class="w-4 h-4"></i><span>启动军师分析 (Jev心智解码)</span>`;
      if (window.lucide) lucide.createIcons();
    }
  }

  // 5. 渲染分析结果
  function renderAnalysisResult(data) {
    if (!data.success) {
      alert('分析异常: ' + (data.error || '未知错误'));
      return;
    }

    // 耗时更新
    latencyBadge.textContent = `⚡ 0.2s 极速判决 · 全流程耗时: ${data.latency_ms} ms ${data.is_mock ? '(离线高保真)' : '(Jev + DeepSeek在线)'}`;

    // A. 渲染对话气泡
    renderBubbles(data.dialogue);

    // B. 渲染 Jev 系统一决策
    const jev = data.jev;
    valStrategy.innerHTML = `<span>${jev.primary_strategy}</span>`;
    valStrategyDesc.textContent = jev.strategy_explanation || '';

    valIntent.innerHTML = `<span>${jev.hidden_intent}</span>`;
    valEmotion.textContent = `情绪状态：${jev.emotional_state || '平稳'}`;

    if (jev.is_shit_test) {
      valShitTest.innerHTML = `<span class="text-amber-600">检测到测试 ⚠️</span>`;
      valShitTestProb.textContent = `置信度: ${(jev.shit_test_prob * 100).toFixed(0)}% (建议化解反撩)`;
    } else {
      valShitTest.innerHTML = `<span class="text-emerald-600">正常交流 ✅</span>`;
      valShitTestProb.textContent = `置信度: ${(jev.shit_test_prob * 100).toFixed(0)}% (无设防陷阱)`;
    }

    // 动态进度条
    numInterest.textContent = `${jev.interest_score}分`;
    barInterest.style.width = `${jev.interest_score}%`;

    numDefense.textContent = `${jev.defense_score}分`;
    barDefense.style.width = `${jev.defense_score}%`;

    numPower.textContent = `${jev.power_dynamic}%`;
    barPower.style.width = `${jev.power_dynamic}%`;

    // C. 渲染三阶实战话术
    renderReplies(data.replies);

    // D. 渲染分支预判
    if (data.branch) {
      branchCard.classList.remove('hidden');
      branchPos.textContent = data.branch.if_positive || '--';
      branchNeu.textContent = data.branch.if_neutral || '--';
      branchNeg.textContent = data.branch.if_cooling || '--';
    }

    if (window.lucide) lucide.createIcons();
  }

  function renderBubbles(dialogue) {
    bubbleList.innerHTML = '';
    if (!dialogue || dialogue.length === 0) {
      dialogueCount.textContent = '0 条消息';
      return;
    }
    dialogueCount.textContent = `共还原 ${dialogue.length} 条`;

    dialogue.forEach(msg => {
      const wrapper = document.createElement('div');
      wrapper.className = `flex flex-col ${msg.is_me ? 'items-end' : 'items-start'}`;

      const meta = document.createElement('span');
      meta.className = 'text-[10px] text-slate-400 mb-0.5 px-1';
      meta.textContent = `${msg.is_me ? '我' : msg.sender}${msg.time ? ' ' + msg.time : ''}`;

      const bubble = document.createElement('div');
      if (msg.is_me) {
        bubble.className = 'max-w-[85%] px-3.5 py-2 rounded-2xl rounded-tr-xs bg-wechat text-white text-xs leading-relaxed shadow-xs';
      } else {
        bubble.className = 'max-w-[85%] px-3.5 py-2 rounded-2xl rounded-tl-xs bg-slate-100 text-slate-800 text-xs leading-relaxed shadow-xs border border-slate-200/60';
      }
      bubble.textContent = msg.text;

      wrapper.appendChild(meta);
      wrapper.appendChild(bubble);
      bubbleList.appendChild(wrapper);
    });

    bubbleList.scrollTop = bubbleList.scrollHeight;
  }

  function renderReplies(replies) {
    replyList.innerHTML = '';
    if (!replies || replies.length === 0) return;

    const tierStyles = {
      '稳健走心版': {
        badgeBg: 'bg-emerald-100 text-emerald-800',
        cardBorder: 'hover:border-emerald-300'
      },
      '高情商策略版': {
        badgeBg: 'bg-pink-100 text-pink-800',
        cardBorder: 'hover:border-pink-300'
      },
      '设立边界版': {
        badgeBg: 'bg-purple-100 text-purple-800',
        cardBorder: 'hover:border-purple-300'
      }
    };

    replies.forEach((rep, idx) => {
      const style = tierStyles[rep.tier] || { badgeBg: 'bg-slate-100 text-slate-800', cardBorder: 'hover:border-slate-300' };

      const card = document.createElement('div');
      card.className = `p-4 rounded-xl border border-slate-200 bg-white transition shadow-xs ${style.cardBorder} flex flex-col space-y-2 relative`;

      const header = document.createElement('div');
      header.className = 'flex items-center justify-between';
      header.innerHTML = `
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded text-xs font-bold ${style.badgeBg}">${rep.tier}</span>
          <span class="text-[11px] text-slate-400">⏰ ${rep.timing || '适时发送'}</span>
        </div>
        <button class="btnCopy px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 flex items-center gap-1 transition active:scale-95" data-content="${encodeURIComponent(rep.content)}">
          <i data-lucide="copy" class="w-3.5 h-3.5"></i>
          <span>一键复制</span>
        </button>
      `;

      const textBody = document.createElement('div');
      textBody.className = 'text-xs text-slate-800 font-medium bg-slate-50/80 p-2.5 rounded-lg border border-slate-100 select-all';
      textBody.textContent = rep.content;

      const rationale = document.createElement('p');
      rationale.className = 'text-[11px] text-slate-500 leading-normal flex items-start gap-1';
      rationale.innerHTML = `<span class="text-pink-500 font-bold shrink-0">💡 心理学设计：</span><span>${rep.rationale}</span>`;

      card.appendChild(header);
      card.appendChild(textBody);
      card.appendChild(rationale);
      replyList.appendChild(card);
    });

    // 绑定一键复制功能
    document.querySelectorAll('.btnCopy').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const textToCopy = decodeURIComponent(btn.getAttribute('data-content'));
        try {
          await navigator.clipboard.writeText(textToCopy);
          btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i><span class="text-emerald-600 font-bold">已复制!</span>`;
          setTimeout(() => {
            btn.innerHTML = `<i data-lucide="copy" class="w-3.5 h-3.5"></i><span>一键复制</span>`;
            if (window.lucide) lucide.createIcons();
          }, 2000);
        } catch (err) {
          // 降级复制
          const textarea = document.createElement('textarea');
          textarea.value = textToCopy;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
          btn.innerHTML = `<span>已复制!</span>`;
        }
      });
    });
  }

  // 6. 配置弹窗处理
  btnSettings.addEventListener('click', async () => {
    modalConfig.classList.remove('hidden');
    try {
      const res = await fetch('/api/config');
      const cfg = await res.json();
      cfgJevUrl.value = cfg.jev_base_url || 'https://api.typesafe.ai/v1';
      cfgLlmUrl.value = cfg.llm_base_url || 'https://api.openai.com/v1';
      cfgLlmModel.value = cfg.llm_model || 'deepseek-chat';
      if (cfg.jev_configured) cfgJevKey.placeholder = `已配置密钥: ${cfg.jev_key_masked}`;
      if (cfg.llm_configured) cfgLlmKey.placeholder = `已配置密钥: ${cfg.llm_key_masked}`;
    } catch (e) {
      console.error(e);
    }
  });

  const closeModal = () => modalConfig.classList.add('hidden');
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);

  btnSaveConfig.addEventListener('click', async () => {
    const payload = {
      jev_api_key: cfgJevKey.value || undefined,
      jev_base_url: cfgJevUrl.value || undefined,
      llm_api_key: cfgLlmKey.value || undefined,
      llm_base_url: cfgLlmUrl.value || undefined,
      llm_model: cfgLlmModel.value || undefined
    };

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        alert('配置保存成功！');
        closeModal();
      }
    } catch (err) {
      alert('保存失败: ' + err.message);
    }
  });

  // 7. 历史记录查看
  const btnHistory = document.getElementById('btnHistory');
  btnHistory.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/history');
      const data = await res.json();
      if (data.items && data.items.length > 0) {
        const item = data.items[0];
        renderAnalysisResult({
          success: true,
          dialogue: item.dialogue_parsed,
          jev: item.jev_analysis,
          replies: item.llm_reply.replies,
          branch: item.llm_reply.branch,
          latency_ms: 0,
          is_mock: true
        });
        alert('已重新载入最近一次历史复盘分析！');
      } else {
        alert('暂无历史记录，快去分析一条对话吧！');
      }
    } catch (err) {
      alert('加载历史失败: ' + err.message);
    }
  });
});
