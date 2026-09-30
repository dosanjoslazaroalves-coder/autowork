import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

function run(command, args) {
  const result = spawnSync(command, args, { stdio: "inherit", shell: false });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}

run(process.execPath, ["scripts/clean.mjs"]);
run(process.execPath, ["node_modules/typescript/bin/tsc"]);
if (existsSync("build/icon.ico")) {
  console.info("Reutilizando build/icon.ico existente.");
} else {
  run(process.execPath, ["scripts/generate-icon.mjs"]);
}
run(process.execPath, ["scripts/copy-assets.mjs"]);
