// node round2/src/build.mjs -> writes ../site (publish: index.html is a fragment) and ../preview (all full documents)
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { PAGES, SITE_CSS, SITE_JS, pageHtml } from "./site2.mjs";
import { CONTENT } from "./pages.mjs";
import "./pages-b.mjs";
import "./pages-c.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const only = process.argv.find((a) => a.startsWith("--only="))?.slice(7);
for (const dir of ["site", "preview"]) {
  mkdirSync(join(ROOT, dir), { recursive: true });
  writeFileSync(join(ROOT, dir, "site.css"), SITE_CSS);
  writeFileSync(join(ROOT, dir, "site.js"), SITE_JS);
}
for (const page of PAGES) {
  if (only && !page.file.startsWith(only)) continue;
  const make = CONTENT[page.file];
  if (!make) { console.log("skip", page.file); continue; }
  const { body, script } = make(page);
  const isIndex = page.file === "index.html";
  writeFileSync(join(ROOT, "site", page.file), pageHtml(page, { body, script, full: !isIndex }));
  writeFileSync(join(ROOT, "preview", page.file), pageHtml(page, { body, script, full: true }));
  console.log("wrote", page.file);
}
