namespace AutoworkRenderer {
  export type UiView = "home" | "memory" | "history" | "settings";
  export type UiTheme = "dark" | "light";
  export type OrbState = "idle" | "listening" | "processing" | "speaking" | "executing" | "success" | "error";

  export interface HistoryItem {
    id: string;
    title: string;
    detail: string;
    time: string;
    state: OrbState;
  }

  export interface UiState {
    view: UiView;
    theme: UiTheme;
    animations: boolean;
    sidebarCollapsed: boolean;
    sidebarOpen: boolean;
    micEnabled: boolean;
    orbState: OrbState;
    activity: string;
    activityTime: string;
    history: HistoryItem[];
  }
}
