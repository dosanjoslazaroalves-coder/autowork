namespace AutoworkRenderer {
  const orbCopy: Record<OrbState, { badge: string; status: string; stage: string }> = {
    idle: { badge: "IDLE", status: "Pronto", stage: "PRONTO PARA VOCÊ" },
    listening: { badge: "LISTENING", status: "Ouvindo...", stage: "OUVINDO AGORA" },
    processing: { badge: "PROCESSING", status: "Processando...", stage: "ORGANIZANDO SINAIS" },
    speaking: { badge: "SPEAKING", status: "Falando...", stage: "EM COMUNICAÇÃO" },
    executing: { badge: "EXECUTING", status: "Executando...", stage: "EM EXECUÇÃO" },
    success: { badge: "SUCCESS", status: "Concluído", stage: "TUDO PRONTO" },
    error: { badge: "ERROR", status: "Erro", stage: "ALGO PRECISA DE ATENÇÃO" }
  };

  export function renderOrb(state: UiState): void {
    const shell = document.querySelector<HTMLElement>("#app-shell");
    const stage = document.querySelector<HTMLElement>("#orb-stage");
    const badge = document.querySelector<HTMLElement>("#orb-state-badge");
    const status = document.querySelector<HTMLElement>("#status-text");
    const stageLabel = document.querySelector<HTMLElement>("#orb-stage-label");
    if (!shell || !stage || !badge || !status || !stageLabel) return;

    const copy = orbCopy[state.orbState];
    shell.dataset.state = state.orbState;
    shell.classList.toggle("no-animations", !state.animations);
    stage.dataset.state = state.orbState;
    stage.setAttribute("aria-label", `Estado visual: ${copy.status}`);
    badge.textContent = copy.badge;
    status.textContent = copy.status;
    stageLabel.textContent = copy.stage;

    document.querySelectorAll<HTMLButtonElement>("[data-state-choice]").forEach((button) => {
      const selected = button.dataset.stateChoice === state.orbState;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  }
}
