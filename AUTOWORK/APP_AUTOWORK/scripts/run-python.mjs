import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const appRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const corePath = resolve(process.env.AUTOWORK_CORE_PATH || join(appRoot, "..", "Chat", "AUTOWORK"));
const python = process.env.PYTHON_EXECUTABLE || join(corePath, ".venv", "Scripts", "python.exe");
if (!existsSync(python)) throw new Error(`Python do núcleo não encontrado: ${python}. Defina PYTHON_EXECUTABLE.`);
const result = spawnSync(python, process.argv.slice(2), {
  cwd: appRoot,
  env: { ...process.env, AUTOWORK_CORE_PATH: corePath, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8", PYTHONUNBUFFERED: "1" },
  stdio: "inherit",
  windowsHide: true
});
if (result.error) throw result.error;
process.exit(result.status ?? 1);
