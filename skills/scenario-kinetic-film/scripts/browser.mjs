// browser.mjs: shared by render.mjs, info.mjs and snap.mjs. Finds Playwright (the film folder first),
// launches Chrome with the flags a frame-exact capture needs, and opens the film served at FILM_URL.
// Playwright loads only when launch() runs, so the other scripts print their usage without it.
import { createRequire } from "module";
import { execSync } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const SKILL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

// where to look, in order: FILM_DIR (set by the Python scripts), the current folder, the skill, a global install
export function playwrightBases(env = process.env, cwd = process.cwd()) {
  const bases = [env.FILM_DIR, cwd, SKILL]
    .filter(Boolean)
    .map((b) => path.resolve(b) + path.sep);
  try {
    bases.push(
      execSync("npm root -g", { stdio: ["ignore", "pipe", "ignore"] })
        .toString()
        .trim() + path.sep,
    );
  } catch {}
  return bases;
}
export function findPlaywright(bases = playwrightBases()) {
  for (const b of bases) {
    try {
      return createRequire(b)("playwright");
    } catch {}
  }
  return null;
}
export const MISSING =
  "Playwright not found. In the film folder run: npm ci (new_film.sh does it), and npx playwright install chromium if Google Chrome is not installed.";

// --run-all-compositor-stages-before-draw: without it, big 3D layers are captured half rastered
export async function launch() {
  const pw = findPlaywright();
  if (!pw) {
    console.error(MISSING);
    process.exit(2);
  }
  const args = [
    "--run-all-compositor-stages-before-draw",
    "--disable-checker-imaging",
    "--ignore-gpu-blocklist",
    "--enable-gpu",
  ];
  if (process.platform === "darwin") args.push("--use-angle=metal");
  try {
    return await pw.chromium.launch({ channel: "chrome", args });
  } catch {
    return await pw.chromium.launch({ args });
  }
}
export const FILM_URL = (
  process.env.FILM_URL || "http://127.0.0.1:5671/"
).replace(/\/?$/, "/");

// headless Chrome keeps about 90 px of window chrome: a 1920x1080 viewport would paint only ~990 px of the stage.
// The film always sets window.__ready, with window.__problems when it could not build; a page error before
// that (a syntax error in spec.js) ends the wait at once instead of after the timeout.
export async function openFilm(b, dsf = 1, render = true) {
  const pg = await b.newPage({
    viewport: { width: 1920, height: 1300 },
    deviceScaleFactor: +dsf,
  });
  const errs = [];
  let crashed;
  const crash = new Promise((r) => (crashed = r));
  pg.on("pageerror", (e) => {
    errs.push("PAGE " + e.message);
    crashed();
  });
  pg.on("console", (m) => {
    if (m.type() === "error" && !/favicon|404/.test(m.text()))
      errs.push("CONSOLE " + m.text());
  });
  await pg.goto(FILM_URL + "index.html" + (render ? "?render=1" : ""));
  const ready = pg
    .waitForFunction(() => window.__ready, null, { timeout: 120000 })
    .catch((e) => errs.push("TIMEOUT " + e.message));
  await Promise.race([
    ready,
    crash.then(() => new Promise((r) => setTimeout(r, 1000))),
  ]);
  const problems = await pg
    .evaluate(() => window.__problems || [])
    .catch(() => []);
  return { pg, errs, problems };
}
export const isMain = (url) =>
  !!process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(url);
