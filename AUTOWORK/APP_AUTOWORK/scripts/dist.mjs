import { createRequire } from "node:module";
import { copyFileSync, existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const appRoot = dirname(dirname(fileURLToPath(import.meta.url)));
process.chdir(appRoot);
const sidecarPath = join(appRoot, "python", "autowork-api.exe");
if (!existsSync(sidecarPath) || statSync(sidecarPath).size === 0) {
  throw new Error("Missing Python sidecar. Run pnpm run build:sidecar before packaging.");
}
const pnpmStore = join(appRoot, "node_modules", ".pnpm");
const builderUtilPackage = readdirSync(pnpmStore).find((entry) => entry.startsWith("builder-util@26."));
if (!builderUtilPackage) throw new Error("builder-util dependency was not found");
const builderUtil = require(join(pnpmStore, builderUtilPackage, "node_modules", "builder-util"));
const originalExec = builderUtil.exec;

// Preserve the Windows environment when NSIS extracts the uninstaller.
builderUtil.exec = (file, args, options = {}) => originalExec(file, args, {
  ...options,
  env: { ...process.env, ...(options.env ?? {}) }
});

const directoryOnly = process.argv.includes("--dir");
const { build } = await import("electron-builder");
await build({ win: directoryOnly ? ["dir"] : ["nsis", "portable"] });
const packagedSidecar = join(appRoot, "release", "win-unpacked", "resources", "autowork", "autowork-api.exe");
if (!existsSync(packagedSidecar) || statSync(packagedSidecar).size !== statSync(sidecarPath).size) {
  throw new Error("The packaged application does not contain the expected Python sidecar.");
}
if (!directoryOnly) {
  const { version } = JSON.parse(readFileSync(join(appRoot, "package.json"), "utf8"));
  const installerName = `AUTOWORK_${version}-Setup.exe`;
  const source = join(appRoot, "release", installerName);
  if (!existsSync(source) || statSync(source).size === 0) throw new Error(`Installer not found: ${source}`);
  const destination = join(appRoot, installerName);
  copyFileSync(source, destination);
  console.info(`Installer copied to ${destination}`);
}
