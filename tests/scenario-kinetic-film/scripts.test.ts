// The node scripts without a browser: finding Playwright, the shutter window, info.mjs's verdict, snap
// times, and the usage messages render.mjs and snap.mjs print before they load anything.
import { spawnSync } from "child_process";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "fs";
import os from "os";
import path from "path";
import { afterAll, describe, expect, it } from "vitest";
import {
  findPlaywright,
  MISSING,
  playwrightBases,
} from "../../skills/scenario-kinetic-film/scripts/browser.mjs";
import { verdict } from "../../skills/scenario-kinetic-film/scripts/info.mjs";
import { shutterWindow } from "../../skills/scenario-kinetic-film/scripts/render.mjs";
import {
  stillName,
  toSeconds,
  USAGE,
} from "../../skills/scenario-kinetic-film/scripts/snap.mjs";

const SCRIPTS = path.resolve(
  __dirname,
  "../../skills/scenario-kinetic-film/scripts",
);
const tmp = mkdtempSync(path.join(os.tmpdir(), "kinetic-scripts-"));
afterAll(() => rmSync(tmp, { recursive: true, force: true }));

function fakePlaywright(name: string) {
  const dir = path.join(tmp, name);
  mkdirSync(path.join(dir, "node_modules", "playwright"), { recursive: true });
  writeFileSync(
    path.join(dir, "node_modules", "playwright", "index.js"),
    `module.exports = { found: ${JSON.stringify(name)} };`,
  );
  return dir;
}

describe("findPlaywright", () => {
  it("looks in FILM_DIR, then the current folder, then the skill, then the global install", () => {
    const bases = playwrightBases({ FILM_DIR: "/films/a" }, "/work");
    expect(bases.slice(0, 3)).toEqual([
      `/films/a${path.sep}`,
      `/work${path.sep}`,
      path.resolve(SCRIPTS, "..") + path.sep,
    ]);
    expect(playwrightBases({}, "/work")[0]).toBe(`/work${path.sep}`);
  });

  it("takes the first install it finds", () => {
    const film = fakePlaywright("film"),
      cwd = fakePlaywright("cwd"),
      empty = path.join(tmp, "empty");
    mkdirSync(empty, { recursive: true });
    expect(findPlaywright([film + path.sep, cwd + path.sep])).toEqual({
      found: "film",
    });
    expect(findPlaywright([empty + path.sep, cwd + path.sep])).toEqual({
      found: "cwd",
    });
    expect(findPlaywright([empty + path.sep])).toBeNull();
  });

  it("says how to install it", () => {
    expect(MISSING).toMatch(/npm ci/);
    expect(MISSING).toMatch(/npx playwright install chromium/);
  });
});

describe("shutterWindow", () => {
  const dt = 0.5 / 60;
  it("opens forward from the frame time", () => {
    expect(shutterWindow(1, dt, 1, [])).toEqual([1, 1 + dt]);
    expect(shutterWindow(1, dt, 3.4, [0.5, 2])).toEqual([1, 1 + 3.4 * dt]);
  });

  it("slides back, keeping its width, when a cut falls inside", () => {
    const [a, b] = shutterWindow(1, dt, 3.4, [1 + dt]);
    expect(b).toBeCloseTo(1 + dt - 1e-4, 12);
    expect(b - a).toBeCloseTo(3.4 * dt, 12);
    expect(a).toBeLessThan(1);
  });

  it("never reaches back across a cut", () => {
    const [a, b] = shutterWindow(1, dt, 3.4, [1 - dt, 1 + dt]);
    expect(a).toBe(1 - dt);
    expect(b).toBeCloseTo(1 + dt - 1e-4, 12);
  });

  it("never spans a cut, wherever the cuts fall", () => {
    for (let i = 0; i < 500; i++) {
      const t = (i * 7.31) % 30,
        sh = 1 + (i % 5);
      const cuts = [t - 0.01 * (i % 3), t + 0.003 * (i % 7), t + 0.02].filter(
        (c) => c > 0,
      );
      const [a, b] = shutterWindow(t, dt, sh, cuts);
      for (const c of cuts)
        expect(c > a && c < b, `t=${t} cut=${c} window=[${a}, ${b}]`).toBe(
          false,
        );
      expect(b).toBeGreaterThan(a);
    }
  });
});

describe("info.mjs verdict", () => {
  const film = { dur: 2 };
  it("fails a film that did not build, with its reasons", () => {
    const v = verdict(null, [
      {
        level: "error",
        msg: "scene 1 (Words 0-8) shot 2: style 'nope' is not one of punch3d",
      },
    ]);
    expect(v.code).toBe(1);
    expect(v.lines).toEqual([
      "the film did not load:",
      "error: scene 1 (Words 0-8) shot 2: style 'nope' is not one of punch3d",
    ]);
  });

  it("fails on page errors when the page gave no reason", () => {
    const v = verdict(null, [], ["PAGE SyntaxError: Unexpected token"]);
    expect(v.code).toBe(1);
    expect(v.lines).toContain("PAGE SyntaxError: Unexpected token");
    expect(verdict(null).lines).toContain("the page set no film and no reason");
  });

  it("passes a film with warnings, and prints them", () => {
    const v = verdict(film, [{ level: "warning", msg: "fps is 30" }]);
    expect(v).toEqual({ code: 0, lines: ["warning: fps is 30"] });
    expect(verdict(film, [], []).code).toBe(0);
  });

  it("fails an error even when a film object exists", () => {
    expect(verdict(film, [{ level: "error", msg: "fonts missing" }]).code).toBe(
      1,
    );
  });
});

describe("snap.mjs times", () => {
  it("reads seconds and beats", () => {
    expect(toSeconds("12.5", 120)).toBe(12.5);
    expect(toSeconds("b4", 120)).toBe(2);
    expect(toSeconds("b12.5", 172)).toBeCloseTo((12.5 * 60) / 172, 12);
    expect(toSeconds("soon", 120)).toBeNaN();
    expect(stillName(2)).toBe("t_002.00.png");
    expect(stillName(45.678)).toBe("t_045.68.png");
  });
});

describe("usage, before any browser", () => {
  // run from an empty folder with no Playwright anywhere it would look first
  const run = (script: string, dir = SCRIPTS) =>
    spawnSync(process.execPath, [path.join(dir, script)], {
      cwd: tmp,
      env: { PATH: process.env.PATH },
      encoding: "utf8",
    });
  // the skills CLI installs a skill as a symlink for some agents
  const linked = path.join(tmp, "linked-scripts");
  symlinkSync(SCRIPTS, linked, "dir");

  for (const [where, dir] of [
    ["", SCRIPTS],
    [" through a symlinked folder", linked],
  ]) {
    it(`render.mjs${where}`, () => {
      const r = run("render.mjs", dir);
      expect(r.status).toBe(1);
      expect(r.stderr).toContain(
        "usage: node render.mjs <dsf> <frame0> <frame1>",
      );
      expect(r.stderr).not.toContain("Playwright");
    });

    it(`snap.mjs${where}`, () => {
      const r = run("snap.mjs", dir);
      expect(r.status).toBe(1);
      expect(r.stderr).toContain(USAGE);
    });
  }
});
