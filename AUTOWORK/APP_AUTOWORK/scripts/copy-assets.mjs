import { cp, mkdir } from "node:fs/promises";

await mkdir("dist/renderer/components", { recursive: true });
await cp("src/renderer/index.html", "dist/renderer/index.html");
await cp("src/renderer/style.css", "dist/renderer/style.css");
await cp("build/icon.ico", "dist/icon.ico");
