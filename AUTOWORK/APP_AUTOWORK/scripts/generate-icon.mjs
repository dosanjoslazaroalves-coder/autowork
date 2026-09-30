import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const appRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const sizes = [16, 32, 48, 64, 128, 256];

// Rasterize the existing artwork with Chromium; never replace the SVG identity
// with a separately drawn icon. Electron is already a build dependency.
if (!process.versions.electron) {
  const environment = { ...process.env };
  delete environment.ELECTRON_RUN_AS_NODE;
  const result = spawnSync(require("electron"), [fileURLToPath(import.meta.url)], {
    cwd: appRoot,
    env: environment,
    stdio: "inherit",
    windowsHide: true
  });
  if (result.error) throw result.error;
  process.exit(result.status ?? 1);
}

const { app, BrowserWindow } = await import("electron");
app.disableHardwareAcceleration();
app.setPath("userData", join(appRoot, ".tmp", "icon-build-profile"));
await app.whenReady();

let window;
try {
  const source = await readFile(join(appRoot, "build", "icon.svg"));
  window = new BrowserWindow({
    show: false,
    webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false }
  });
  await window.loadURL("data:text/html,<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; img-src data:\">");
  const images = await window.webContents.executeJavaScript(`(async () => {
    const artwork = new Image();
    artwork.src = ${JSON.stringify(`data:image/svg+xml;base64,${source.toString("base64")}`)};
    await artwork.decode();
    return ${JSON.stringify(sizes)}.map((size) => {
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = size;
      canvas.getContext("2d").drawImage(artwork, 0, 0, size, size);
      return { size, base64: canvas.toDataURL("image/png").split(",")[1] };
    });
  })()`);
  const header = Buffer.alloc(6);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(images.length, 4);
  let offset = 6 + images.length * 16;
  const payloads = images.map(({ size, base64 }) => {
    const data = Buffer.from(base64, "base64");
    if (data.readUInt32BE(16) !== size || data.readUInt32BE(20) !== size) {
      throw new Error(`Invalid PNG dimensions for ${size}px icon`);
    }
    return { size, data };
  });
  const entries = payloads.map(({ size, data }) => {
    const entry = Buffer.alloc(16);
    entry[0] = entry[1] = size === 256 ? 0 : size;
    entry.writeUInt16LE(1, 4);
    entry.writeUInt16LE(32, 6);
    entry.writeUInt32LE(data.length, 8);
    entry.writeUInt32LE(offset, 12);
    offset += data.length;
    return entry;
  });
  await mkdir(join(appRoot, "build"), { recursive: true });
  await writeFile(join(appRoot, "build", "icon.ico"), Buffer.concat([
    header, ...entries, ...payloads.map(({ data }) => data)
  ]));
  console.info("AUTOWORK icon generated from build/icon.svg (16–256px).");
} catch (error) {
  console.error(error);
  process.exitCode = 1;
} finally {
  window?.destroy();
  app.exit(process.exitCode ?? 0);
}
