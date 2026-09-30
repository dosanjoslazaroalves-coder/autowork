import { app, BrowserWindow, ipcMain } from "electron";
import { ChildProcessWithoutNullStreams, execFile, spawn } from "node:child_process";
import { createConnection } from "node:net";
import * as fs from "node:fs";
import * as path from "node:path";

type AutoworkStatus = {
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
};

const DEFAULT_API_HOST = "127.0.0.1";
const DEFAULT_API_PORT = 47100;
const STARTUP_TIMEOUT_MS = 90000;
const REQUEST_TIMEOUT_MS = 5000;
const COMMAND_TIMEOUT_MS = 120000;
type ConnectionState = "connecting" | "ready" | "processing" | "error";
let connectionState: ConnectionState = "connecting";
let connectionError = "";
let logStream: fs.WriteStream | undefined;

function reportConnection(state: ConnectionState, error?: string): void {
  if (state === connectionState && (error || "") === connectionError) return;
  log(error ? "error" : "info", `[Electron] Estado: ${state}${error ? " · " + error : ""}`);
  connectionState = state;
  connectionError = error || "";
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send("autowork:connection", { state, error });
}

function describeError(error: unknown): string {
  return error instanceof Error && error.cause ? `${error.message}: ${String(error.cause)}` : String(error);
}

function log(level: "info" | "warn" | "error", message: string): void {
  console[level](message);
  logStream?.write(new Date().toISOString() + " " + level.toUpperCase() + " " + message + "\n");
}

function initializeLogs(): void {
  const directory = path.join(app.getPath("userData"), "logs");
  fs.mkdirSync(directory, { recursive: true });
  const filename = path.join(directory, "desktop.log");
  if (fs.existsSync(filename) && fs.statSync(filename).size > 5 * 1024 * 1024) {
    fs.copyFileSync(filename, filename + ".previous");
    fs.truncateSync(filename);
  }
  logStream = fs.createWriteStream(filename, { flags: "a", encoding: "utf8" });
  logStream.on("error", (error) => {
    console.error("[AUTOWORK] Não foi possível gravar o log:", error);
    logStream = undefined;
  });
  log("info", "[Electron] Desktop " + app.getVersion() + " · " + (app.isPackaged ? "instalado" : "desenvolvimento") + " · app=" + app.getAppPath() + " · log=" + filename);
}

class AutoworkApiProcess {
  private child?: ChildProcessWithoutNullStreams;
  private startPromise?: Promise<void>;
  private ownsChild = false;
  private stopPromise?: Promise<void>;
  private closing = false;
  private commandPending = false;
  private lastProbeError = "API ainda não respondeu";
  private readonly host = this.readHost();
  private readonly port = this.readPort();

  async health(): Promise<{ status: string }> {
    await this.ensureStarted();
    return this.getJson("/health") as Promise<{ status: string }>;
  }

  async status(): Promise<AutoworkStatus> {
    try {
      await this.ensureStarted();
      // The first status request loads the real core; allow its cold start.
      const status = await this.getJson("/api/status", STARTUP_TIMEOUT_MS) as AutoworkStatus;
      const ready = status.api === "online" && status.ready === true && status.core === "online";
      if (status.error || status.core === "offline") reportConnection("error", status.error || "Núcleo offline");
      else reportConnection(this.commandPending ? "processing" : ready ? "ready" : "connecting");
      return status;
    } catch (error) {
      reportConnection("error", describeError(error));
      throw error;
    }
  }

  async command(texto: string): Promise<unknown> {
    const textoLimpo = texto.trim();
    if (!textoLimpo || textoLimpo.length > 4000) throw new Error("O comando deve ter entre 1 e 4000 caracteres.");
    if (this.commandPending) throw new Error("Aguarde a conclusão do comando em andamento.");
    this.commandPending = true;
    try {
      await this.ensureStarted();
      reportConnection("processing");
      log("info", "[Main] enviando POST /api/command: " + textoLimpo);
      return await this.postJson("/api/command", { texto: textoLimpo });
    } catch (error) {
      log("error", "[AUTOWORK] Falha no comando: " + String(error));
      reportConnection("error", describeError(error));
      throw error;
    } finally {
      this.commandPending = false;
    }
  }

  async request(action: string, payload?: unknown): Promise<unknown> {
    if (action === "health") return this.health();
    if (action === "ping") return { message: "pong", pid: process.pid };
    if (action === "status") return this.status();
    if (action === "command") {
      if (typeof payload !== "string") throw new Error("Command payload must be text");
      return this.command(payload);
    }
    throw new Error(`Unsupported AUTOWORK API action: ${action}`);
  }

  shutdown(): Promise<void> {
    this.closing = true;
    return this.stop();
  }

  async stop(): Promise<void> {
    if (this.stopPromise) return this.stopPromise;
    const child = this.child;
    if (!child || !this.ownsChild) return;
    this.stopPromise = this.stopOwnedChild(child).finally(() => {
      this.stopPromise = undefined;
    });
    return this.stopPromise;
  }

  private async stopOwnedChild(child: ChildProcessWithoutNullStreams): Promise<void> {
    if (child.exitCode !== null || child.signalCode !== null || !child.pid) return;
    const waitForExit = (timeoutMs: number): Promise<boolean> => new Promise((resolve) => {
      if (child.exitCode !== null || child.signalCode !== null) return resolve(true);
      const onExit = (): void => { clearTimeout(timer); resolve(true); };
      const timer = setTimeout(() => { child.removeListener("exit", onExit); resolve(false); }, timeoutMs);
      child.once("exit", onExit);
    });
    log("info", "[AUTOWORK] Encerrando API própria PID=" + child.pid);
    if (!child.stdin.destroyed && child.stdin.writable) child.stdin.write("shutdown\n");
    if (await waitForExit(5000)) return;
    // Only the process handle spawned by this instance is eligible for forced cleanup.
    if (process.platform === "win32") {
      await new Promise<void>((resolve, reject) => {
        const killer = spawn("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true });
        killer.once("error", reject);
        killer.once("exit", (code) => {
          if (code !== 0 && child.exitCode === null && child.signalCode === null) {
            reject(new Error("Falha ao encerrar árvore da API própria (taskkill " + code + ")."));
          } else resolve();
        });
      });
    } else child.kill("SIGTERM");
    if (!await waitForExit(5000)) throw new Error("A API própria não confirmou encerramento.");
  }

  private async ensureStarted(): Promise<void> {
    await this.start();
  }

  async start(): Promise<void> {
    if (this.closing) throw new Error("O AUTOWORK está encerrando.");
    if (this.stopPromise) await this.stopPromise;
    if (!this.startPromise) {
      this.startPromise = (async () => {
        if (await this.isApiReady()) {
          if (!this.child && connectionState === "connecting") log("info", "[FastAPI] Reutilizando API AUTOWORK válida em " + this.baseUrl);
          return;
        }
        if (this.closing) throw new Error("O AUTOWORK está encerrando.");
        if (this.child && this.ownsChild) {
          await this.waitUntilReady(() => undefined);
          return;
        }
        if (await this.isPortOpen()) {
          await this.logPortOwner();
          throw new Error(`Porta ${this.port} ocupada; /health não confirmou AUTOWORK: ${this.lastProbeError}`);
        }
        reportConnection("connecting");
        await this.spawnAndWait();
      })().catch(async (error) => {
        await this.logPortOwner();
        reportConnection("error", describeError(error));
        throw error;
      }).finally(() => { this.startPromise = undefined; });
    }
    await this.startPromise;
  }

  private async spawnAndWait(): Promise<void> {
    const packagedExecutable = path.join(process.resourcesPath, "autowork", "autowork-api.exe");
    const executableOverride = !app.isPackaged ? process.env.AUTOWORK_API_EXECUTABLE : undefined;
    const developmentCorePath = path.resolve(app.getAppPath(), "..", "Chat", "AUTOWORK");
    const corePath = !app.isPackaged ? (process.env.AUTOWORK_CORE_PATH || developmentCorePath) : "";
    const scriptPath = app.isPackaged
      ? path.join(process.resourcesPath, "autowork", "api.py")
      : path.resolve(__dirname, "..", "python", "api.py");
    const corePython = corePath ? path.join(corePath, ".venv", "Scripts", "python.exe") : "";
    const environment: NodeJS.ProcessEnv = {
      ...process.env,
      AUTOWORK_API_HOST: this.host,
      AUTOWORK_API_PORT: String(this.port),
      ...(corePath ? { AUTOWORK_CORE_PATH: corePath } : {}),
      PYTHONUNBUFFERED: "1",
      PYTHONUTF8: "1",
      PYTHONIOENCODING: "utf-8",
      AUTOWORK_PARENT_PID: String(process.pid),
      AUTOWORK_DATA_DIR: app.getPath("userData")
    };
    if (app.isPackaged) {
      delete environment.AUTOWORK_CORE_PATH;
      delete environment.PYTHONPATH;
      delete environment.PYTHONHOME;
      if (!fs.existsSync(packagedExecutable)) {
        throw new Error("O componente AUTOWORK não foi encontrado na instalação. Reinstale o aplicativo.");
      }
    }
    if (this.closing) throw new Error("O AUTOWORK está encerrando.");

    if (executableOverride || app.isPackaged) {
      const executable = executableOverride || packagedExecutable;
      log("info", "[FastAPI] spawn " + JSON.stringify({ executable, args: [], cwd: app.getPath("userData"), port: this.port }));
      this.child = spawn(executable, [], {
        cwd: app.getPath("userData"),
        env: environment,
        windowsHide: true,
        stdio: "pipe"
      });
    } else {
      const python = process.env.PYTHON_EXECUTABLE
        || corePython;
      if (!python || !fs.existsSync(python)) throw new Error(`Python do núcleo não encontrado: ${python}. Configure PYTHON_EXECUTABLE com o caminho do .venv.`);
      log("info", "[FastAPI] spawn " + JSON.stringify({ executable: python, args: [scriptPath], cwd: path.dirname(scriptPath), port: this.port, corePath }));
      this.child = spawn(python, [scriptPath], {
        cwd: path.dirname(scriptPath),
        env: environment,
        windowsHide: true,
        stdio: "pipe"
      });
    }
    this.ownsChild = true;
    const child = this.child;
    child.stdin.on("error", (error) => log("warn", "[AUTOWORK API] stdin: " + String(error)));

    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      const message = chunk.trim();
      if (message) log("info", `[FastAPI stdout] ${message}`);
    });
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk: string) => {
      const message = chunk.trim();
      if (message) log("warn", `[FastAPI stderr] ${message}`);
    });
    let startupError: Error | undefined;
    child.once("error", (error) => {
      startupError = error;
      if (this.child === child) { this.child = undefined; this.ownsChild = false; }
      log("error", "[AUTOWORK] Falha ao iniciar API local: " + String(error));
    });
    child.once("exit", (code, signal) => {
      if (!startupError) {
        startupError = new Error(`process exited (code=${code}, signal=${signal ?? "none"})`);
      }
      if (this.child === child) {
        this.child = undefined;
        this.ownsChild = false;
      }
      log("info", `[AUTOWORK API] exited (code=${code}, signal=${signal ?? "none"})`);
      if (!this.closing && !this.stopPromise) reportConnection("error", `FastAPI encerrou (code=${code}, signal=${signal ?? "none"})`);
    });

    log("info", `[FastAPI] iniciando em ${this.baseUrl} · PID=${child.pid}`);
    try {
      await this.waitUntilReady(() => startupError);
    } catch (error) {
      await this.stop();
      throw new Error(`Local AUTOWORK API did not become ready: ${String(error)}`);
    }
  }

  private async waitUntilReady(getStartupError: () => Error | undefined): Promise<void> {
    const deadline = Date.now() + STARTUP_TIMEOUT_MS;
    let lastError = this.lastProbeError;
    let attempt = 0;
    while (Date.now() < deadline) {
      if (this.closing) throw new Error("O AUTOWORK está encerrando.");
      const startupError = getStartupError();
      if (startupError) throw startupError;
      try {
        log("info", `[FastAPI] Tentativa ${++attempt} GET ${this.baseUrl}/health (limite ${STARTUP_TIMEOUT_MS} ms)`);
        if (await this.isApiReady()) {
          log("info", "[FastAPI] /health confirmou API AUTOWORK pronta");
          return;
        }
        lastError = this.lastProbeError;
      } catch (error) {
        // HTTP responses from an incompatible service are terminal, not retries.
        throw error;
      }
      log("warn", `[FastAPI] Tentativa ${attempt} falhou: ${lastError}`);
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
    const startupError = getStartupError();
    if (startupError) throw startupError;
    throw new Error(lastError);
  }

  private async isApiReady(): Promise<boolean> {
    let health: { status?: unknown; service?: unknown; protocol?: unknown; frozen?: unknown };
    try {
      health = await this.getJson("/health") as typeof health;
    } catch (error) {
      this.lastProbeError = describeError(error);
      if (error instanceof TypeError || (error instanceof Error &&
        (error.name === "AbortError" || (error.cause instanceof Error && error.cause.name === "AbortError")))) return false;
      throw new Error("A porta " + this.port + " está ocupada por uma API incompatível: " + String(error));
    }
    if (!health || health.status !== "ok" || health.service !== "AUTOWORK" || health.protocol !== 1) {
      throw new Error("A porta " + this.port + " está ocupada por um serviço incompatível com AUTOWORK.");
    }
    if (app.isPackaged && health.frozen !== true) {
      throw new Error("Encerre a API de desenvolvimento na porta " + this.port + " antes de abrir o AUTOWORK instalado.");
    }
    return true;
  }

  private isPortOpen(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      const socket = createConnection({ host: this.host, port: this.port });
      socket.setTimeout(1500);
      socket.once("connect", () => { socket.destroy(); resolve(true); });
      socket.once("timeout", () => { socket.destroy(); reject(new Error("Timeout ao verificar porta " + this.port)); });
      socket.once("error", (error: NodeJS.ErrnoException) => {
        socket.destroy();
        if (error.code === "ECONNREFUSED") resolve(false); else reject(error);
      });
    });
  }

  private async logPortOwner(): Promise<void> {
    if (process.platform !== "win32") return;
    await new Promise<void>((resolve) => {
      execFile("netstat.exe", ["-ano", "-p", "tcp"], { windowsHide: true, timeout: 3000 }, (error, stdout) => {
        if (error) log("warn", "[FastAPI] Diagnóstico da porta: " + String(error));
        for (const line of stdout.split(/\r?\n/)) {
          const columns = line.trim().split(/\s+/);
          if (columns[1]?.endsWith(":" + this.port) && columns[2]?.endsWith(":0")) log("warn", `[FastAPI] Porta ${this.port} ocupada: ${line.trim()} (última coluna: PID)`);
        }
        resolve();
      });
    });
  }

  private async getJson(endpoint: string, timeoutMs = REQUEST_TIMEOUT_MS): Promise<unknown> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: { Accept: "application/json" },
        signal: controller.signal
      });
      const body = await response.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(body);
      } catch {
        parsed = body;
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${typeof parsed === "string" ? parsed : JSON.stringify(parsed)}`);
      return parsed;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") throw new Error(`Timeout GET ${endpoint} após ${timeoutMs} ms`, { cause: error });
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  private async postJson(endpoint: string, body: unknown): Promise<unknown> {
    const started = Date.now();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), COMMAND_TIMEOUT_MS);
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body),
        signal: controller.signal
      });
      const rawBody = await response.text();
      let parsed: unknown;
      try {
        parsed = JSON.parse(rawBody);
      } catch {
        parsed = rawBody;
      }
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${typeof parsed === "string" ? parsed : JSON.stringify(parsed)}`);
      log("info", `[Main] POST ${endpoint} HTTP ${response.status} em ${Date.now() - started} ms`);
      return parsed;
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("O núcleo excedeu o tempo de resposta. O comando pode continuar em execução; verifique o estado antes de enviar novamente.");
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  private readHost(): string {
    const host = process.env.AUTOWORK_API_HOST || DEFAULT_API_HOST;
    if (!["127.0.0.1", "localhost", "::1"].includes(host)) {
      throw new Error("AUTOWORK_API_HOST deve apontar para o computador local.");
    }
    return host;
  }

  private readPort(): number {
    const port = Number(process.env.AUTOWORK_API_PORT || DEFAULT_API_PORT);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new Error("AUTOWORK_API_PORT must be an integer between 1 and 65535");
    }
    return port;
  }

  private get baseUrl(): string {
    const host = this.host.includes(":") ? `[${this.host}]` : this.host;
    return `http://${host}:${this.port}`;
  }
}

let mainWindow: BrowserWindow | undefined;
const autowork = new AutoworkApiProcess();
const hasSingleInstanceLock = app.requestSingleInstanceLock();
if (!hasSingleInstanceLock) app.quit();
app.on("second-instance", () => {
  if (mainWindow?.isMinimized()) mainWindow.restore();
  mainWindow?.focus();
});

function createWindow(): void {
  mainWindow = new BrowserWindow({
    title: "AUTOWORK 0.3",
    width: 1100,
    height: 760,
    minWidth: 820,
    minHeight: 560,
    autoHideMenuBar: true,
    backgroundColor: "#101827",
    icon: path.join(__dirname, "icon.ico"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  mainWindow.webContents.on("preload-error", (_event, preloadPath, error) => {
    log("error", `[Preload] Falha em ${preloadPath}: ${error.stack || error.message}`);
  });
  mainWindow.webContents.on("console-message", (details) => {
    log(details.level === "error" ? "error" : details.level === "warning" ? "warn" : "info", `${details.message} (${details.sourceId}:${details.lineNumber})`);
  });
  mainWindow.webContents.on("render-process-gone", (_event, details) => log("error", "[Renderer] Processo encerrou: " + JSON.stringify(details)));
  mainWindow.webContents.on("did-fail-load", (_event, code, description) => log("error", `[Renderer] Falha ao carregar: ${code} ${description}`));
  void mainWindow.loadFile(path.join(__dirname, "renderer", "index.html")).catch((error) => log("error", "[Renderer] " + String(error)));
  mainWindow.on("closed", () => {
    mainWindow = undefined;
  });
}

app.whenReady().then(() => {
  if (!hasSingleInstanceLock) return;
  try { initializeLogs(); } catch (error) { console.error("[AUTOWORK] Falha ao preparar logs:", error); }
  app.setAppUserModelId("com.autowork.desktop");

  ipcMain.handle("app:info", () => ({
    name: "AUTOWORK",
    version: app.getVersion(),
    packaged: app.isPackaged
  }));

  ipcMain.handle("autowork:request", async (_event, action: unknown, payload?: unknown) => {
    if (typeof action !== "string" || !/^[a-z][a-z0-9._-]{0,63}$/i.test(action)) {
      throw new Error("Invalid AUTOWORK action");
    }
    return autowork.request(action, payload);
  });

  ipcMain.handle("autowork:health", () => autowork.health());
  ipcMain.handle("autowork:ping", () => {
    log("info", "[IPC] renderer → preload → main: pong");
    return { message: "pong", pid: process.pid };
  });
  ipcMain.handle("autowork:status", () => autowork.status());
  ipcMain.handle("autowork:command", async (_event, texto: unknown) => {
    if (typeof texto !== "string") throw new Error("Command text must be a string");
    log("info", "[IPC] comando recebido: " + texto);
    return autowork.command(texto);
  });

  ipcMain.handle("autowork:stop", () => autowork.stop());
  createWindow();
  void autowork.status().catch((error) => {
    log("error", "[AUTOWORK] Falha na inicialização da API: " + String(error));
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

let quitPending = false;
let shutdownComplete = false;
app.on("before-quit", (event) => {
  if (shutdownComplete) return;
  event.preventDefault();
  if (quitPending) return;
  quitPending = true;
  void autowork.shutdown().catch((error) => {
    log("error", "[AUTOWORK] Falha no encerramento da API: " + String(error));
  }).finally(() => {
    shutdownComplete = true;
    if (logStream) logStream.end(() => app.quit()); else app.quit();
  });
});
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
