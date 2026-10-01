const store = new AutoworkRenderer.UiStore(
  AutoworkRenderer.createInitialState(AutoworkRenderer.getStoredTheme())
);

const viewTitles: Record<AutoworkRenderer.UiView, string> = {
  home: "Visão geral",
  memory: "Memória",
  history: "Histórico",
  settings: "Configurações"
};

const stateActivity: Record<AutoworkRenderer.OrbState, string> = {
  idle: "Aguardando comando",
  listening: "Microfone visual ativado",
  processing: "Sinais em processamento",
  speaking: "Resposta visual em andamento",
  executing: "Demonstração em execução",
  success: "Demonstração concluída",
  error: "Estado de atenção visual"
};

const stateActivityTime: Record<AutoworkRenderer.OrbState, string> = {
  idle: "Agora",
  listening: "Neste momento",
  processing: "Agora",
  speaking: "Agora",
  executing: "Agora",
  success: "Agora há pouco",
  error: "Agora"
};

let flowTimers: number[] = [];
let commandPending = false;
let coreBusy = false;
let visualPreview = false;
let statusRequestPending = false;
let statusTimer = 0;
let commandRevision = 0;
let rendererClosed = false;
let lastConnectionError = "";
let lastConnectionLabel = "";
let lastCoreStatus = "";
let bridgeReady = false;
let coreReady = false;
let voiceRequestPending = false;
let unsubscribeConnection: (() => void) | undefined;

// This map only represents states reported by the Python core.
const coreVisualStates: Record<string, AutoworkRenderer.OrbState> = {
  INICIALIZANDO: "processing", IDLE: "idle", OUVINDO: "listening",
  TRANSCREVENDO: "processing", DETECTANDO_WAKE: "listening", PROCESSANDO: "processing",
  EXECUTANDO: "executing", FALANDO: "speaking", SUCESSO: "success", ERRO: "error", ENCERRANDO: "processing"
};

function syncCommandControls(): void {
  const busy = commandPending || coreBusy;
  const voiceRunning = store.getState().micEnabled;
  const button = document.querySelector<HTMLButtonElement>("#command-button");
  if (button) {
    button.disabled = busy || voiceRequestPending || voiceRunning || !bridgeReady || !coreReady;
    button.textContent = busy ? "Processando…" : "Enviar ↗";
  }
  document.querySelector("#command-form")?.setAttribute("aria-busy", String(busy));
  document.querySelector(".command-card")?.classList.toggle("is-processing", busy);
  document.querySelectorAll<HTMLButtonElement>("[data-state-choice], #demo-flow-button").forEach((control) => { control.disabled = busy || voiceRunning; });
  const micButton = document.querySelector<HTMLButtonElement>("#mic-button");
  if (micButton) micButton.disabled = voiceRequestPending || !bridgeReady || !coreReady;
  const stopButton = document.querySelector<HTMLButtonElement>("#stop-button");
  if (stopButton) stopButton.disabled = voiceRequestPending || (!voiceRunning && busy);
}

function updateActivity(state: AutoworkRenderer.OrbState, customText?: string): void {
  store.update({
    orbState: state,
    activity: customText ?? stateActivity[state],
    activityTime: stateActivityTime[state]
  });
}

function addHistoryItem(state: AutoworkRenderer.OrbState): void {
  const item: AutoworkRenderer.HistoryItem = {
    id: `${state}-${Date.now()}`,
    title: stateActivity[state],
    detail: "Interação visual da sessão",
    time: "Agora",
    state
  };
  store.update((current) => ({ history: [item, ...current.history].slice(0, 8) }));
}

function clearFlowTimers(): void {
  flowTimers.forEach((timer) => window.clearTimeout(timer));
  flowTimers = [];
}

function setConnectionStatus(online: boolean, label: string): void {
  const transition = `${online}:${label}`;
  if (transition !== lastConnectionLabel) console.info("[Renderer] Conexão:", label, "disponível=" + online);
  lastConnectionLabel = transition;
  const pill = document.querySelector<HTMLElement>("#connection-pill");
  const dot = pill?.querySelector<HTMLElement>(".status-dot");
  const text = document.querySelector<HTMLElement>("#connection-text");
  if (dot) dot.classList.toggle("ready", online);
  if (text) text.textContent = label;
  pill?.setAttribute("aria-label", label);
  if (pill) pill.dataset.online = String(online);
}

function receiveConnectionUpdate(update: AutoworkConnectionUpdate): void {
  console.info("[Renderer] Evento do main:", JSON.stringify(update));
  if (update.state === "connecting") {
    coreReady = false;
    setConnectionStatus(false, "Conectando...");
    if (!commandPending) updateActivity("processing", "Conectando à API local");
  } else if (update.state === "processing") {
    coreBusy = true;
    setConnectionStatus(coreReady, "Processando");
    updateActivity("processing", "Comando recebido pelo Electron");
  } else if (update.state === "error") {
    coreReady = false;
    coreBusy = false;
    setConnectionStatus(false, "Erro de conexão");
    updateActivity("error", update.error || "Falha na comunicação com a API local");
  } else if (update.state === "ready") {
    // Transport readiness is not core readiness: only /api/status enables commands.
    if (!coreReady) setConnectionStatus(false, "Inicializando núcleo");
    window.clearTimeout(statusTimer);
    void loadAutoworkStatus();
  }
  syncCommandControls();
}

async function loadAutoworkStatus(): Promise<void> {
  if (statusRequestPending || rendererClosed || !bridgeReady) return;
  statusRequestPending = true;
  const revision = commandRevision;
  try {
    const status = await window.electronAPI.getAutoworkStatus();
    if (revision !== commandRevision) return;
    const online = status.api === "online";
    const ready = status.ready ?? (status.autowork === "online" && status.core !== "offline");
    const state = (status.state ?? (ready ? "IDLE" : "INICIALIZANDO")).toUpperCase();
    const failed = Boolean(status.error) || status.core === "offline";
    const voiceRunning = Boolean(status.voice_running);
    coreReady = online && ready && !failed;
    coreBusy = coreReady && ["PROCESSANDO", "EXECUTANDO", "FALANDO", "OUVINDO", "TRANSCREVENDO", "DETECTANDO_WAKE"].includes(state);
    if (store.getState().micEnabled !== voiceRunning) store.update({ micEnabled: voiceRunning });
    const transcript = document.querySelector<HTMLElement>("#voice-transcript");
    if (transcript && status.last_transcript) transcript.textContent = `"${status.last_transcript}"`;
    const orbStage = document.querySelector<HTMLElement>("#orb-stage");
    orbStage?.style.setProperty("--audio-level", String(status.audio_level ?? 0));
    const coreStatus = JSON.stringify({ api: status.api, core: status.core, ready, state, error: status.error });
    if (coreStatus !== lastCoreStatus) console.info("[Renderer] Status real do núcleo:", coreStatus);
    lastCoreStatus = coreStatus;
    const label = !online ? "Erro de conexão" : failed ? "Erro no núcleo" : !ready ? "Inicializando núcleo" : commandPending || coreBusy ? "Processando" : "AUTOWORK pronto";
    setConnectionStatus(coreReady, label);
    if ((!visualPreview || commandPending || coreBusy) && !commandPending) {
      const visualState = failed ? "error" : (coreVisualStates[state] ?? "idle");
      updateActivity(visualState, status.error || (state === "IDLE" ? "AUTOWORK pronto para receber comandos" : "Núcleo: " + state));
    } else if (commandPending && coreBusy) {
      updateActivity(coreVisualStates[state] ?? "processing", "Núcleo: " + state);
    }
    lastConnectionError = "";
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setConnectionStatus(false, "Erro de conexão");
    if (!commandPending && !visualPreview) updateActivity("error", "Não foi possível conectar ao AUTOWORK local");
    if (message !== lastConnectionError) console.error("[Renderer] Status indisponível:", message);
    lastConnectionError = message;
    coreReady = false;
    coreBusy = false;
  } finally {
    statusRequestPending = false;
    syncCommandControls();
    if (!rendererClosed) statusTimer = window.setTimeout(() => void loadAutoworkStatus(), store.getState().micEnabled ? 400 : 1500);
  }
}

async function sendRealCommand(): Promise<void> {
  const input = document.querySelector<HTMLTextAreaElement>("#command-input");
  const resultElement = document.querySelector<HTMLElement>("#command-result");
  const texto = input?.value.trim() ?? "";
  if (!texto || !resultElement || commandPending || voiceRequestPending || coreBusy || store.getState().micEnabled || !bridgeReady || !coreReady) return;
  console.info("[Renderer] Comando enviado:", texto);
  commandPending = true;
  commandRevision++;
  visualPreview = false;
  clearFlowTimers();
  store.update({ micEnabled: false });
  syncCommandControls();
  resultElement.textContent = "Processando no núcleo AUTOWORK…";
  updateActivity("processing", "Enviando comando ao núcleo local");
  try {
    const result = await window.electronAPI.sendAutoworkCommand(texto);
    const status = typeof result.status === "string" ? result.status : "desconhecido";
    const action = typeof result.acao === "string" ? result.acao : "comando";
    const message = typeof result.mensagem === "string" ? result.mensagem : "O núcleo não retornou uma mensagem.";
    const succeeded = status === "sucesso";
    console.info("[Renderer] Resposta real:", JSON.stringify({ status, acao: action, mensagem: message }));
    resultElement.textContent = (succeeded ? "Concluído: " : "Não concluído: ") + message;
    const visualState = succeeded ? "success" : "error";
    updateActivity(visualState, action + ": " + message);
    store.update((current) => ({ history: [{ id: "command-" + Date.now(), title: texto, detail: message, time: new Date().toLocaleTimeString("pt-BR"), state: visualState as AutoworkRenderer.OrbState }, ...current.history].slice(0, 8) }));
    if (succeeded && input && input.value.trim() === texto) {
      input.value = "";
      updateCommandCount();
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro de comunicação";
    console.error("[Renderer] Falha no comando:", message);
    resultElement.textContent = "Não foi possível concluir: " + message;
    updateActivity("error", "Falha ao processar comando local");
  } finally {
    commandPending = false;
    commandRevision++;
    syncCommandControls();
    input?.focus();
    window.clearTimeout(statusTimer);
    void loadAutoworkStatus();
  }
}

function updateCommandCount(): void {
  const input = document.querySelector<HTMLTextAreaElement>("#command-input");
  const count = document.querySelector("#command-count");
  if (count) count.textContent = (input?.value.length ?? 0) + " / 4000";
}

async function toggleRealVoice(forceEnabled?: boolean): Promise<void> {
  if (voiceRequestPending || !bridgeReady || !coreReady) return;
  const enabled = forceEnabled ?? !store.getState().micEnabled;
  voiceRequestPending = true;
  syncCommandControls();
  updateActivity(enabled ? "processing" : "idle", enabled ? "Iniciando microfone real" : "Parando microfone real");
  try {
    const status = enabled
      ? await window.electronAPI.startAutoworkVoice()
      : await window.electronAPI.stopAutoworkVoice();
    const voiceRunning = (status as { voice_running?: boolean }).voice_running === true;
    store.update({ micEnabled: voiceRunning });
    updateActivity(voiceRunning ? "listening" : "idle", voiceRunning ? "Microfone real ativo" : "Microfone real parado");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("[Renderer] Falha ao alternar voz:", message);
    updateActivity("error", message);
  } finally {
    voiceRequestPending = false;
    syncCommandControls();
    void loadAutoworkStatus();
  }
}

function runVisualFlow(): void {
  if (commandPending || coreBusy) return;
  visualPreview = true;
  clearFlowTimers();
  const sequence: Array<{ state: AutoworkRenderer.OrbState; delay: number }> = [
    { state: "listening", delay: 0 },
    { state: "processing", delay: 850 },
    { state: "executing", delay: 1700 },
    { state: "success", delay: 2750 },
    { state: "idle", delay: 4050 }
  ];
  sequence.forEach(({ state, delay }) => {
    flowTimers.push(window.setTimeout(() => {
      updateActivity(state);
      if (state === "success") addHistoryItem(state);
    }, delay));
  });
}

function renderHistory(state: AutoworkRenderer.UiState): void {
  const list = document.querySelector<HTMLElement>("#history-list");
  const total = document.querySelector<HTMLElement>("#history-total");
  if (!list || !total) return;
  total.textContent = String(state.history.length);
  if (state.history.length === 0) {
    list.innerHTML = '<div class="history-empty">Nenhum evento registrado ainda.</div>';
    return;
  }
  list.innerHTML = state.history.map((item) => `
    <div class="history-item">
      <span class="history-item-marker" aria-hidden="true"></span>
      <div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.detail)}</span></div>
      <time>${escapeHtml(item.time)}</time>
    </div>
  `).join("");
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[character] ?? character);
}

function render(state: AutoworkRenderer.UiState): void {
  const shell = document.querySelector<HTMLElement>("#app-shell");
  const pageTitle = document.querySelector<HTMLElement>("#page-title");
  const sidebarToggle = document.querySelector<HTMLButtonElement>("#sidebar-toggle");
  const micButton = document.querySelector<HTMLButtonElement>("#mic-button");
  const micLabel = document.querySelector<HTMLElement>("#mic-label");
  const aboutVersion = document.querySelector<HTMLElement>("#about-version");
  if (!shell || !pageTitle || !sidebarToggle || !micButton || !micLabel) return;

  shell.classList.toggle("sidebar-collapsed", state.sidebarCollapsed);
  shell.classList.toggle("sidebar-open", state.sidebarOpen);
  pageTitle.textContent = viewTitles[state.view];
  sidebarToggle.setAttribute("aria-expanded", String(!state.sidebarCollapsed));
  sidebarToggle.setAttribute("aria-label", state.sidebarCollapsed ? "Expandir menu" : "Recolher menu");
  sidebarToggle.title = state.sidebarCollapsed ? "Expandir menu" : "Recolher menu";
  sidebarToggle.innerHTML = `<span aria-hidden="true">${state.sidebarCollapsed ? "›" : "‹"}</span>`;
  micButton.setAttribute("aria-pressed", String(state.micEnabled));
  micButton.classList.toggle("is-active", state.micEnabled);
  micLabel.textContent = state.micEnabled ? "Desativar microfone" : "Ativar microfone";

  document.querySelectorAll<HTMLElement>("[data-view]").forEach((button) => {
    const active = button.dataset.view === state.view;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  });
  document.querySelectorAll<HTMLElement>("[data-view-panel]").forEach((panel) => {
    const active = panel.dataset.viewPanel === state.view;
    panel.classList.toggle("is-active", active);
    panel.toggleAttribute("hidden", !active);
  });
  document.querySelectorAll<HTMLButtonElement>("[data-theme-choice]").forEach((button) => {
    const selected = button.dataset.themeChoice === state.theme;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const activityText = document.querySelector<HTMLElement>("#activity-text");
  const activityTime = document.querySelector<HTMLElement>("#activity-time");
  if (activityText) activityText.textContent = state.activity;
  if (activityTime) activityTime.textContent = state.activityTime;
  const animationToggle = document.querySelector<HTMLInputElement>("#animations-toggle");
  if (animationToggle) animationToggle.checked = state.animations;
  if (aboutVersion && aboutVersion.textContent === "—") {
    aboutVersion.textContent = document.querySelector("#app-version")?.textContent ?? "Interface local";
  }

  AutoworkRenderer.applyTheme(state.theme);
  AutoworkRenderer.renderOrb(state);
  renderHistory(state);
}

function showView(view: AutoworkRenderer.UiView): void {
  store.update({ view, sidebarOpen: false });
}

document.querySelectorAll<HTMLButtonElement>("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    const view = button.dataset.view as AutoworkRenderer.UiView | undefined;
    if (view) showView(view);
  });
});

document.querySelector("#sidebar-toggle")?.addEventListener("click", () => {
  store.update((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
});
document.querySelector("#mobile-menu-button")?.addEventListener("click", () => store.update({ sidebarOpen: true }));
document.querySelector("#sidebar-scrim")?.addEventListener("click", () => store.update({ sidebarOpen: false }));

const orbStage = document.querySelector<HTMLElement>("#orb-stage");
let orbPointerFrame = 0;
orbStage?.addEventListener("pointermove", (event) => {
  if (orbPointerFrame) return;
  orbPointerFrame = window.requestAnimationFrame(() => {
    const bounds = orbStage.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
    const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
    orbStage.style.setProperty("--pointer-x", String(Math.max(-1, Math.min(1, x))));
    orbStage.style.setProperty("--pointer-y", String(Math.max(-1, Math.min(1, y))));
    orbPointerFrame = 0;
  });
});
orbStage?.addEventListener("pointerleave", () => {
  if (orbPointerFrame) window.cancelAnimationFrame(orbPointerFrame);
  orbPointerFrame = 0;
  orbStage.style.setProperty("--pointer-x", "0");
  orbStage.style.setProperty("--pointer-y", "0");
});

document.querySelector("#mic-button")?.addEventListener("click", () => {
  void toggleRealVoice();
});
document.querySelector("#stop-button")?.addEventListener("click", () => {
  if (store.getState().micEnabled) {
    void toggleRealVoice(false);
    return;
  }
  if (commandPending || coreBusy) return;
  visualPreview = false;
  clearFlowTimers();
  store.update({ micEnabled: false });
  updateActivity("idle", "Ação visual interrompida");
  addHistoryItem("idle");
});
document.querySelector("#demo-flow-button")?.addEventListener("click", runVisualFlow);
document.querySelector<HTMLFormElement>("#command-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  void sendRealCommand();
});

document.querySelector<HTMLTextAreaElement>("#command-input")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!event.repeat) void sendRealCommand();
  }
});
document.querySelector("#command-input")?.addEventListener("input", updateCommandCount);
document.querySelectorAll<HTMLButtonElement>("[data-state-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    if (commandPending || coreBusy) return;
    visualPreview = true;
    clearFlowTimers();
    const selectedState = button.dataset.stateChoice as AutoworkRenderer.OrbState | undefined;
    if (!selectedState) return;
    store.update({ micEnabled: selectedState === "listening" });
    updateActivity(selectedState);
    if (selectedState === "success" || selectedState === "error") addHistoryItem(selectedState);
  });
});
document.querySelectorAll<HTMLButtonElement>("[data-theme-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    const theme = button.dataset.themeChoice as AutoworkRenderer.UiTheme | undefined;
    if (theme) store.update({ theme });
  });
});
document.querySelector("#animations-toggle")?.addEventListener("change", (event) => {
  store.update({ animations: (event.target as HTMLInputElement).checked });
});

async function initializeElectronBridge(): Promise<void> {
  console.info("[Renderer] Inicializando comunicação com Electron.");
  setConnectionStatus(false, "Conectando...");
  syncCommandControls();
  try {
    const bridge = window.electronAPI;
    const requiredMethods = ["pingAutowork", "getAppInfo", "getAutoworkStatus", "sendAutoworkCommand", "startAutoworkVoice", "stopAutoworkVoice", "onAutoworkConnection"] as const;
    if (!bridge || requiredMethods.some((method) => typeof bridge[method] !== "function")) {
      throw new Error("A ponte electronAPI está ausente ou desatualizada. Consulte os logs de preload e refaça o build.");
    }
    unsubscribeConnection = bridge.onAutoworkConnection(receiveConnectionUpdate);
    const reply = await bridge.pingAutowork();
    if (reply.message !== "pong") throw new Error("O IPC não retornou o pong esperado.");
    console.info("[Renderer] IPC validado:", JSON.stringify(reply));
    bridgeReady = true;
    void bridge.getAppInfo().then((info) => {
      const label = `v${info.version}${info.packaged ? " · instalado" : " · desenvolvimento"}`;
      const versionElement = document.querySelector<HTMLElement>("#app-version");
      const aboutVersion = document.querySelector<HTMLElement>("#about-version");
      if (versionElement) versionElement.textContent = label;
      if (aboutVersion) aboutVersion.textContent = `v${info.version}`;
    }).catch((error) => console.error("[Renderer] Não foi possível ler a versão:", String(error)));
    await loadAutoworkStatus();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("[Renderer] Falha na inicialização da ponte:", message);
    bridgeReady = false;
    coreReady = false;
    unsubscribeConnection?.();
    unsubscribeConnection = undefined;
    setConnectionStatus(false, "Erro na ponte Electron");
    updateActivity("error", message);
    const result = document.querySelector<HTMLElement>("#command-result");
    if (result) result.textContent = "Não foi possível iniciar a comunicação: " + message;
    syncCommandControls();
  }
}

store.subscribe(render);
void initializeElectronBridge();
window.addEventListener("beforeunload", () => {
  rendererClosed = true;
  window.clearTimeout(statusTimer);
  clearFlowTimers();
  unsubscribeConnection?.();
});
