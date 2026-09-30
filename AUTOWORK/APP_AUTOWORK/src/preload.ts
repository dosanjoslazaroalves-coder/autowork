import { contextBridge, ipcRenderer } from "electron";

type ConnectionUpdate = {
  state: "connecting" | "ready" | "processing" | "error";
  error?: string;
};

contextBridge.exposeInMainWorld("electronAPI", {
  getAppInfo: () => ipcRenderer.invoke("app:info"),
  pingAutowork: () => ipcRenderer.invoke("autowork:ping"),
  getAutoworkHealth: () => ipcRenderer.invoke("autowork:health"),
  getAutoworkStatus: () => ipcRenderer.invoke("autowork:status"),
  sendAutoworkCommand: (texto: string) => {
    console.info("[Preload] Encaminhando comando ao IPC:", texto);
    return ipcRenderer.invoke("autowork:command", texto);
  },
  onAutoworkConnection: (listener: (update: ConnectionUpdate) => void) => {
    const receive = (_event: Electron.IpcRendererEvent, update: ConnectionUpdate): void => listener(update);
    ipcRenderer.on("autowork:connection", receive);
    return () => ipcRenderer.removeListener("autowork:connection", receive);
  },
  requestAutowork: (action: string, payload?: unknown) =>
    ipcRenderer.invoke("autowork:request", action, payload),
  stopAutowork: () => ipcRenderer.invoke("autowork:stop")
});

console.info("[Preload] Ponte electronAPI inicializada.");
