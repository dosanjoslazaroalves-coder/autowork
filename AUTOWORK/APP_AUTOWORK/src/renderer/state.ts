namespace AutoworkRenderer {
  type StateListener = (state: UiState) => void;

  export class UiStore {
    private state: UiState;
    private readonly listeners = new Set<StateListener>();

    constructor(initialState: UiState) {
      this.state = initialState;
    }

    getState(): UiState {
      return this.state;
    }

    subscribe(listener: StateListener): () => void {
      this.listeners.add(listener);
      listener(this.state);
      return () => this.listeners.delete(listener);
    }

    update(change: Partial<UiState> | ((state: UiState) => Partial<UiState>)): void {
      const partialChange = typeof change === "function" ? change(this.state) : change;
      this.state = { ...this.state, ...partialChange };
      for (const listener of this.listeners) listener(this.state);
    }
  }

  export function createInitialState(theme: UiTheme): UiState {
    return {
      view: "home",
      theme,
      animations: true,
      sidebarCollapsed: false,
      sidebarOpen: false,
      micEnabled: false,
      orbState: "idle",
      activity: "Aguardando comando",
      activityTime: "Agora",
      history: []
    };
  }
}
