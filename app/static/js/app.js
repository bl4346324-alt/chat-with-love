// Chat-with-Love 前端交互引擎 · 情圣 (QingSheng) 恋爱 Skill 自动调用驱动
document.addEventListener('DOMContentLoaded', () => {
  // 状态变量
  let currentImageFile = null;
  let currentImageBase64 = null;
  let autoInvokeTimer = null;
  let isAnalyzing = false;
  let autoInvokeEnabled = true;

  // DOM 元素
  const tabPasteImg = document.getElementById('tabPasteImg');
  const tabPasteText = document.getElementById('tabPasteText');
  const viewPasteImg = document.getElementById('viewPasteImg');
  const viewPasteText = document.getElementById('viewPasteText');

  const toggleAutoInvoke = document.getElementById('toggleAutoInvoke');
  const autoInvokeStatus = document.getElementById('autoInvokeStatus');
  const autoInvokePing = document.getElementById('autoInvokePing');
  const autoTypingNotice = document.getElementById('autoTypingNotice');
  const inputCharCount = document.getElementById('inputCharCount');

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

  // 情圣恋爱 Skill UI 组件
  const skillStageBadge = document.getElementById('skillStageBadge');
  const stageGoalText = document.getElementById('stageGoalText');
  const skillSignalType = document.getElementById('skillSignalType');
  const skillSignalDetail = document.getElementById('skillSignalDetail');
  const skillTacticsContainer = document.getElementById('skillTacticsContainer');

  // Jev 系统一组件
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

  // 系统二话术与分支
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

  // 1. 初始化自动调用开关状态
  const savedAutoPref = localStorage.getItem('chat_love_auto_invoke');
  if (savedAutoPref !== null) {
    autoInvokeEnabled = savedAutoPref === 'true';
    toggleAutoInvoke.checked = autoInvokeEnabled;
  }
  updateAutoInvokeUI();

  toggleAutoInvoke.addEventListener('change', () => {
    autoInvokeEnabled = toggleAutoInvoke.checked;
    localStorage.setItem('chat_love_auto_invoke', autoInvokeEnabled);
    updateAutoInvokeUI();
  });

  function updateAutoInvokeUI() {
    if (autoInvokeEnabled) {
      autoInvokeStatus.textContent = '输入聊天或粘贴截图后，自动启动情圣 Skill 分析';
      autoInvokeStatus.className = 'text-[11px] text-pink-600 font-medium';
      autoInvokePing.classList.remove('hidden');
    } else {
      autoInvokeStatus.textContent = '自动调用已暂停，可通过下方按钮手动触发分析';
      autoInvokeStatus.className = 'text-[11px] text-slate-400 font-medium';
      autoInvokePing.classList.add('hidden');
    }
  }

  // 2. 标签切换
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

  // 3. 剪贴板全局粘贴监听 (Cmd+V / Ctrl+V)
  window.addEventListener('paste', (e) => {
    // 如果焦点在文本框内，不拦截图片粘贴，由文本框专用 paste 事件处理文字
    if (document.activeElement === inputText) return;

    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        handleImageSelection(file, true); // true = auto invoke
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
      handleImageSelection(e.target.files[0], true);
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
      handleImageSelection(e.dataTransfer.files[0], true);
    }
  });

  function handleImageSelection(file, shouldAutoTrigger = false) {
    if (!file || !file.type.startsWith('image/')) return;
    currentImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      currentImageBase64 = e.target.result;
      imagePreview.src = currentImageBase64;
      dropPrompt.classList.add('hidden');
      imagePreviewContainer.classList.remove('hidden');
      btnAnalyzeImage.disabled = false;

      // 【核心自动调用】：截图识别后，若开启自动调用，立即触发情圣 Skill 分析
      if (shouldAutoTrigger && autoInvokeEnabled) {
        flashAutoInvokeNotice('⚡ 检测到微信截图，情圣恋爱 Skill 自动启动分析中...');
        triggerImageAnalysis();
      }
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

  // 4. 文本输入与自动调用逻辑
  inputText.addEventListener('input', () => {
    const text = inputText.value;
    inputCharCount.textContent = `${text.length} 字`;

    if (!autoInvokeEnabled || isAnalyzing) return;

    // 清理之前的防抖计时器
    if (autoInvokeTimer) clearTimeout(autoInvokeTimer);

    // 检查是否有有效内容 (至少 6 个字，或者包含换行/对话痕迹)
    const trimmed = text.trim();
    if (trimmed.length >= 6) {
      autoTypingNotice.innerHTML = `<span class="text-pink-600 font-semibold animate-pulse">⚡ 正在捕捉聊天意图... 停止打字 800ms 后自动调用情圣 Skill</span>`;
      autoInvokeTimer = setTimeout(() => {
        autoTypingNotice.innerHTML = `<span class="text-emerald-600 font-semibold">✨ 已自动触发情圣 Skill 军师推演！</span>`;
        triggerTextAnalysis();
      }, 800);
    } else {
      autoTypingNotice.textContent = '✨ 键入对话停顿 800ms 或直接粘贴将自动调用 Skill';
    }
  });

  // 文本框粘贴事件：粘贴后立即无延迟自动调用
  inputText.addEventListener('paste', () => {
    if (!autoInvokeEnabled || isAnalyzing) return;
    if (autoInvokeTimer) clearTimeout(autoInvokeTimer);

    setTimeout(() => {
      const text = inputText.value.trim();
      inputCharCount.textContent = `${text.length} 字`;
      if (text.length >= 4) {
        flashAutoInvokeNotice('⚡ 已捕获粘贴内容，情圣恋爱 Skill 自动调用推演中...');
        triggerTextAnalysis();
      }
    }, 120);
  });

  // 5. 实战案例快速载入与自动调用
  const demoCases = {
    tired: `我: 今天工作顺利吗？\n对方: 别提了，连轴转开了一整天会，整个人都快散架了😭\n对方: 现在刚回到家，动都不想动`,
    cold: `我: 周末这家餐厅看起来不错，一起去尝尝吗？\n对方: 哦\n对方: 随便吧`,
    shittest: `对方: 你平时是不是对所有女生都这么会说话啊？\n对方: 感觉你很像海王哎😏`
  };

  document.querySelectorAll('.btnDemo').forEach(btn => {
    btn.addEventListener('click', () => {
      const caseKey = btn.getAttribute('data-case');
      inputText.value = demoCases[caseKey] || '';
      inputCharCount.textContent = `${inputText.value.length} 字`;
      if (autoInvokeEnabled) {
        flashAutoInvokeNotice(`⚡ 已载入「${btn.textContent}」案例，情圣恋爱 Skill 自动调用分析...`);
        triggerTextAnalysis();
      }
    });
  });

  function flashAutoInvokeNotice(msg) {
    if (autoInvokeStatus) {
      autoInvokeStatus.textContent = msg;
      autoInvokeStatus.className = 'text-[11px] text-pink-700 font-bold animate-pulse';
      setTimeout(updateAutoInvokeUI, 3500);
    }
  }

  // 6. 分析触发器
  btnAnalyzeText.addEventListener('click', () => {
    triggerTextAnalysis();
  });

  btnAnalyzeImage.addEventListener('click', () => {
    triggerImageAnalysis();
  });

  function triggerTextAnalysis() {
    const text = inputText.value.trim();
    if (!text) {
      alert('请先输入或粘贴聊天文字记录');
      return;
    }
    executeAnalysisStream({
      text: text,
      target_alias: inputAlias.value.trim() || '对方',
      user_mbti: inputUserMbti.value.trim(),
      target_mbti: inputTargetMbti.value.trim(),
      auto_invoke: true
    });
  }

  function triggerImageAnalysis() {
    if (!currentImageBase64) return;
    executeAnalysisStream({
      image_base64: currentImageBase64,
      target_alias: inputAlias.value.trim() || '对方',
      user_mbti: inputUserMbti.value.trim(),
      target_mbti: inputTargetMbti.value.trim(),
      auto_invoke: true
    });
  }

  function resetForNewAnalysis() {
    latencyBadge.textContent = '⚡ 情圣恋爱 Skill 启动中... 毫秒级心智解码';
    valStrategy.innerHTML = '<span class="text-pink-400 animate-pulse">研判中...</span>';
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
        <span>情圣 Skill 自动解码完成，大模型打字机流式呈现三阶实战话术...</span>
      </div>
    `;
  }

  function updateSkillUI(skill) {
    if (!skill) return;

    if (skillStageBadge) {
      skillStageBadge.textContent = skill.stage_name;
    }
    if (stageGoalText) {
      stageGoalText.textContent = skill.stage_goal;
    }

    // 更新 7 阶段进度步骤 (1 - 7)
    const stageNum = skill.stage_number || 2;
    for (let i = 1; i <= 7; i++) {
      const stepEl = document.getElementById(`step-${i}`);
      if (!stepEl) continue;
      if (i === stageNum) {
        stepEl.className = 'py-1 rounded bg-pink-500 text-white shadow-xs font-bold transition-all transform scale-105';
      } else if (i < stageNum) {
        stepEl.className = 'py-1 rounded bg-pink-100 text-pink-700 font-semibold transition-all';
      } else {
        stepEl.className = 'py-1 rounded bg-slate-100 text-slate-400 transition-all';
      }
    }

    // 信号展示
    if (skillSignalType) {
      skillSignalType.textContent = skill.signal_type;
      if (skill.signal_type.includes('废物测试')) {
        skillSignalType.className = 'px-2 py-0.2 rounded text-[11px] font-bold bg-amber-100 text-amber-700';
      } else if (skill.signal_type.includes('IOI')) {
        skillSignalType.className = 'px-2 py-0.2 rounded text-[11px] font-bold bg-emerald-100 text-emerald-700';
      } else if (skill.signal_type.includes('IOD')) {
        skillSignalType.className = 'px-2 py-0.2 rounded text-[11px] font-bold bg-rose-100 text-rose-700';
      } else {
        skillSignalType.className = 'px-2 py-0.2 rounded text-[11px] font-bold bg-pink-100 text-pink-700';
      }
    }
    if (skillSignalDetail) {
      skillSignalDetail.textContent = skill.signal_detail;
    }

    // 战术标签
    if (skillTacticsContainer && skill.tactics_suggested) {
      skillTacticsContainer.innerHTML = '';
      skill.tactics_suggested.forEach(t => {
        const tag = document.createElement('span');
        tag.className = 'px-2 py-0.5 rounded bg-white text-pink-700 border border-pink-200 text-[11px] font-medium shadow-2xs';
        tag.textContent = `#${t.replace(/^#/, '')}`;
        skillTacticsContainer.appendChild(tag);
      });
    }
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
            <span>情圣正在推演话术...</span>
          </span>
        </div>
        <div class="card-content text-xs text-slate-800 font-medium bg-slate-50/80 p-2.5 rounded-lg border border-slate-100 min-h-[46px] leading-relaxed select-all">
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

  // 7. SSE 流式通信管道 (全自动调用执行引擎)
  async function executeAnalysisStream(payload) {
    if (isAnalyzing) return;
    isAnalyzing = true;
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
        buffer = lines.pop();

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

              } else if (currentEvent === 'skill') {
                // 【核心】：接收到情圣 Skill 研判事件，瞬间更新 UI 进度与信号
                updateSkillUI(data.skill);

              } else if (currentEvent === 'jev') {
                jevReceived = true;
                const jev = data.jev;
                latencyBadge.textContent = `⚡ 情圣 Skill + Jev决策 (${data.latency_ms} ms)`;

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

                // 三维心理雷达滑竿
                numInterest.textContent = `${jev.interest_score}分`;
                barInterest.style.width = `${jev.interest_score}%`;

                numDefense.textContent = `${jev.defense_score}分`;
                barDefense.style.width = `${jev.defense_score}%`;

                numPower.textContent = `${jev.power_dynamic}%`;
                barPower.style.width = `${jev.power_dynamic}%`;

                // 立即点亮三阶话术打字机卡片骨架
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
      isAnalyzing = false;
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    btnAnalyzeText.disabled = isLoading;
    btnAnalyzeImage.disabled = isLoading;
    if (isLoading) {
      btnAnalyzeText.innerHTML = `<span class="animate-spin mr-2">⏳</span> 正在极速推演与打字流式输出...`;
      btnAnalyzeImage.innerHTML = `<span class="animate-spin mr-2">⏳</span> 正在极速推演与打字流式输出...`;
    } else {
      btnAnalyzeText.innerHTML = `<i data-lucide="sparkle" class="w-4 h-4"></i><span>手动触发军师分析 (情圣Skill驱动)</span>`;
      btnAnalyzeImage.innerHTML = `<i data-lucide="sparkle" class="w-4 h-4"></i><span>手动触发军师分析 (情圣Skill驱动)</span>`;
      if (window.lucide) lucide.createIcons();
    }
  }

  // 8. 完整结果渲染
  function renderAnalysisResult(data) {
    if (!data.success) {
      alert('分析异常: ' + (data.error || '未知错误'));
      return;
    }

    // 耗时更新
    latencyBadge.textContent = `⚡ 情圣 Skill 判决完成 · 全流程耗时: ${data.latency_ms} ms ${data.is_mock ? '(情圣离线知识库)' : '(在线模型驱动)'}`;

    // A. 渲染对话气泡
    renderBubbles(data.dialogue);

    // B. 更新 Skill UI
    if (data.skill_insight) {
      updateSkillUI(data.skill_insight);
    }

    // C. 渲染 Jev 系统一决策
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

    // D. 渲染三阶实战话术
    renderReplies(data.replies);

    // E. 渲染分支预判
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

    replies.forEach((rep) => {
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
      textBody.className = 'text-xs text-slate-800 font-medium bg-slate-50/80 p-2.5 rounded-lg border border-slate-100 select-all leading-relaxed';
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
      btn.addEventListener('click', async () => {
        const textToCopy = decodeURIComponent(btn.getAttribute('data-content'));
        try {
          await navigator.clipboard.writeText(textToCopy);
          btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-600"></i><span class="text-emerald-600 font-bold">已复制!</span>`;
          setTimeout(() => {
            btn.innerHTML = `<i data-lucide="copy" class="w-3.5 h-3.5"></i><span>一键复制</span>`;
            if (window.lucide) lucide.createIcons();
          }, 2000);
        } catch (err) {
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

  // 9. 配置弹窗处理
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

  // 10. 历史记录查看
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
          skill_insight: item.skill_insight || null,
          replies: item.llm_reply.replies,
          branch: item.llm_reply.branch,
          latency_ms: 0,
          is_mock: true
        });
        alert('已重新载入最近一次历史复盘分析！');
      } else {
        alert('暂无历史记录，快去输入一条对话体验自动调用吧！');
      }
    } catch (err) {
      alert('加载历史失败: ' + err.message);
    }
  });
});
