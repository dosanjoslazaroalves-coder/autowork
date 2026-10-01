export {};

declare global {
  interface AutoworkConnectionUpdate {
    state: "connecting" | "ready" | "processing" | "error";
    error?: string;
  }

  interface Window {
    electronAPI: {
      getAppInfo: () => Promise<{
        name: string;
        version: string;
        packaged: boolean;
      }>;
      pingAutowork: () => Promise<{ message: "pong"; pid: number }>;
      onAutoworkConnection: (listener: (update: AutoworkConnectionUpdate) => void) => () => void;
      getAutoworkHealth: () => Promise<{
        status: string;
      }>;
      getAutoworkStatus: () => Promise<{
        api: string;
        autowork: string;
        mode?: string;
        service?: string;
        pid?: number;
        time?: string;
        state?: string;
        core?: string;
        ready?: boolean;
         error?: string;
         voice_running?: boolean;
         last_transcript?: string;
         last_response?: Record<string, unknown>;
         audio_level?: number;
       }>;
       sendAutoworkCommand: (texto: string) => Promise<Record<string, unknown>>;
       startAutoworkVoice: () => Promise<Record<string, unknown>>;
       stopAutoworkVoice: () => Promise<Record<string, unknown>>;
      requestAutowork: (action: string, payload?: unknown) => Promise<unknown>;
      stopAutowork: () => Promise<void>;
    };
  }
}
