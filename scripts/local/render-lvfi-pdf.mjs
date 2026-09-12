import { createRequire } from "node:module";
import { readFile, stat, writeFile } from "node:fs/promises";

// Resolve a Chromium installed beside the locked Playwright dependency; callers
// may still override this for a managed local installation.
process.env.PLAYWRIGHT_BROWSERS_PATH ??= "0";
const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error("usage: render-lvfi-pdf.mjs INPUT.html OUTPUT.pdf");
await stat(input);
const require = createRequire(new URL("../../apps/web/package.json", import.meta.url));
const { chromium } = require("playwright");
const browser = await chromium.launch({
  headless: true,
});
try {
  const page = await browser.newPage();
  await page.setContent(await readFile(input, "utf8"), { waitUntil: "load" });
  await page.pdf({ path: output, format: "A4", printBackground: true, preferCSSPageSize: true });
} finally {
  await browser.close();
}
// Chromium stamps the wall-clock time in the document information dictionary.
// Normalize only those volatile bytes so an immutable snapshot and template yield
// the same artifact bytes without altering the rendered page content.
const generated = await readFile(output);
const normalized = generated
  .toString("latin1")
  .replace(/\/(CreationDate|ModDate) \(D:\d{14}[+-]\d{2}'\d{2}'\)/g, "/$1 (D:19700101000000+00'00')");
await writeFile(output, Buffer.from(normalized, "latin1"));
