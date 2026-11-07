import { afterEach, describe, expect, it, vi } from "vitest";
import {
  resetState,
  restoreGlobals,
  setGlobal,
  state,
  three,
} from "./engine-fakes";

// main.js boots a WebGL page: three, its addons and the browser globals are fakes that
// record what reached them, while the engine's canvas, layer and post logic runs for real.
vi.mock("three", async () => (await import("./engine-fakes")).three);
vi.mock("three/addons/postprocessing/EffectComposer.js", async () => ({
  EffectComposer: (await import("./engine-fakes")).addons.EffectComposer,
}));
vi.mock("three/addons/postprocessing/TexturePass.js", async () => ({
  TexturePass: (await import("./engine-fakes")).addons.TexturePass,
}));
vi.mock("three/addons/postprocessing/UnrealBloomPass.js", async () => ({
  UnrealBloomPass: (await import("./engine-fakes")).addons.UnrealBloomPass,
}));
vi.mock("three/addons/postprocessing/ShaderPass.js", async () => ({
  ShaderPass: (await import("./engine-fakes")).addons.ShaderPass,
}));
vi.mock("three/addons/loaders/TTFLoader.js", async () => ({
  TTFLoader: (await import("./engine-fakes")).addons.TTFLoader,
}));
vi.mock("three/addons/loaders/FontLoader.js", async () => ({
  Font: (await import("./engine-fakes")).addons.Font,
}));
vi.mock("three/addons/geometries/TextGeometry.js", () => ({
  TextGeometry: class {},
}));

// The project's timeline.js only exists once a project is scaffolded. vitest keys a
// module it cannot resolve by its raw specifier, so the mock uses main.js's own.
const TIMELINE_ID = "./timeline.js";
const MAIN = "../../skills/scenario-kinetic-music-video/assets/engine/main.js";

const AUDIO = {
  duration: 4,
  bpm: 120,
  env_fps: 60,
  env: { mix: [0, 1, 0] },
  beats: [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
  downbeats: [0, 2],
  kicks: [0, 1],
};
const LYRICS = { lines: [] };

type Scene = {
  load?: (E: Engine, l: Layer) => unknown;
  prepare?: (E: Engine, t: number, l: Layer) => unknown;
  render: (E: Engine, t: number, rt: unknown, l: Layer) => unknown;
};
type Layer = {
  id: string;
  scene: Scene;
  loaded: boolean;
  [k: string]: unknown;
};
type Engine = Record<string, any>;
type Page = {
  win: Record<string, any>;
  E: Engine;
  canvas: Record<string, any>;
  fetched: string[];
  fontLoads: string[];
  frameCallbacks: (() => unknown)[];
  errors: unknown[];
};

const scene = (log: string[] = [], name = "", op?: unknown): Scene => ({
  load: vi.fn(),
  prepare: (_E, t) => log.push(`prepare:${name}@${t}`),
  render: (_E, t) => {
    log.push(`render:${name}@${t}`);
    return op;
  },
});

async function boot({
  search = "",
  timeline = {},
  scenes = {},
}: {
  search?: string;
  timeline?: Record<string, unknown>;
  scenes?: Record<string, Scene>;
} = {}): Promise<Page> {
  vi.resetModules();
  resetState();
  const win: Record<string, any> = {};
  const fetched: string[] = [];
  const fontLoads: string[] = [];
  const frameCallbacks: (() => unknown)[] = [];
  const errors: unknown[] = [];
  const canvas: Record<string, any> = {
    width: 0,
    height: 0,
    style: {},
    toBlob(cb: (b: Blob) => void, type: string, q: number) {
      canvas.blobArgs = [type, q];
      cb(new Blob([new Uint8Array([7, 8, 9])]));
    },
  };
  setGlobal("window", win);
  setGlobal("location", { search });
  setGlobal("document", {
    getElementById: (id: string) => (id === "c" ? canvas : null),
    fonts: {
      load: async (f: string) => fontLoads.push(f),
      ready: Promise.resolve(),
    },
  });
  setGlobal("fetch", async (url: string) => {
    fetched.push(url);
    return { json: async () => (url.endsWith("audio.json") ? AUDIO : LYRICS) };
  });
  setGlobal("requestAnimationFrame", (cb: () => unknown) =>
    frameCallbacks.push(cb),
  );
  vi.spyOn(console, "error").mockImplementation((e) => errors.push(e));
  vi.doMock(TIMELINE_ID, () => ({
    CANVAS: undefined,
    SAFE: undefined,
    POST: undefined,
    HUD: undefined,
    TIMELINE: [],
    ...timeline,
  }));
  for (const [file, s] of Object.entries(scenes))
    vi.doMock(`/engine/scenes/${file}`, () => ({ default: s }));
  await import(MAIN);
  await vi.waitFor(() => {
    if (!win.__ready && !win.__error) throw new Error("still booting");
  });
  return { win, E: win.E, canvas, fetched, fontLoads, frameCallbacks, errors };
}

const finalUniforms = () =>
  state.composers[0].passes[2].uniforms as Record<string, { value: any }>;
const bloom = () => state.composers[0].passes[1] as Record<string, number>;

afterEach(() => {
  restoreGlobals();
  vi.restoreAllMocks();
});

describe("canvas", () => {
  it("scales the canvas and rounds each side to an even number", async () => {
    const { E, canvas } = await boot({ search: "?canvas=1080x1350&scale=0.5" });
    expect([canvas.width, canvas.height]).toEqual([540, 676]);
    expect(canvas.style).toEqual({ width: "540px", height: "676px" });
    expect([E.W, E.H, E.SCALE]).toEqual([540, 676, 0.5]);
    expect(E.CANVAS).toEqual([1080, 1350]);
    expect(E.ORIENT).toBe("portrait");
    expect(state.renderers[0].calls).toContainEqual([
      "setSize",
      540,
      676,
      false,
    ]);
    expect(state.composers[0].size).toEqual([540, 676]);
  });

  it("takes the canvas and safe band from timeline.js when the query names none", async () => {
    const { E } = await boot({
      timeline: { CANVAS: "portrait", SAFE: { portrait: { top: 0.2 } } },
    });
    expect([E.W, E.H]).toEqual([1080, 1920]);
    expect(E.SAFE).toEqual({ x: 65, y: 384, w: 875, h: 864 });
  });

  it("orients from the canvas, not the scaled size", async () => {
    // 2x2 rounds to an even square at this scale, but the canvas is still landscape
    const { E } = await boot({ search: "?canvas=1920x1080&scale=0.0001" });
    expect([E.W, E.H]).toEqual([2, 2]);
    expect(E.ORIENT).toBe("landscape");
  });

  it("reports an unreadable canvas through window.__error and refuses to render", async () => {
    const { win, canvas, errors } = await boot({ search: "?canvas=vertical" });
    expect(win.__error).toMatch(/vertical/);
    expect(win.__ready).toBeUndefined();
    expect(errors).toHaveLength(1);
    expect(canvas.width).toBe(1920);
    await expect(win.renderFrame(0)).rejects.toThrow(/vertical/);
  });

  it("centers a camera on the safe band only when the band is inset", async () => {
    const portrait = await boot({ search: "?canvas=portrait&safe" });
    const cam = new three.PerspectiveCamera();
    expect(portrait.E.safeCamera(cam)).toBe(cam);
    expect(cam.viewOffset).toEqual([
      1080,
      1920,
      540 - (65 + 875 / 2),
      960 - (269 + 979 / 2),
      1080,
      1920,
    ]);
    expect(portrait.E.debugSafe).toBe(true);

    const landscape = await boot();
    const flat = new three.PerspectiveCamera();
    landscape.E.safeCamera(flat);
    expect(flat.viewOffset).toBeNull();
    expect(landscape.E.debugSafe).toBe(false);
  });
});

describe("boot", () => {
  it("loads the song, the fonts and every scene before it reports ready", async () => {
    const hud = scene();
    const { win, E, fetched, fontLoads } = await boot({
      timeline: { TIMELINE: [{ id: "hud", start: 0, end: 99, z: 100 }] },
      scenes: { "hud.js": hud },
    });
    expect(win.__ready).toBe(true);
    expect(win.__error).toBeUndefined();
    expect(fetched).toEqual([
      "/engine/data/audio.json",
      "/engine/data/lyrics.json",
    ]);
    expect(E.dur).toBe(4);
    expect(E.bpm).toBe(120);
    expect(E.beat(2.25).bar).toBe(1);
    expect(fontLoads).toHaveLength(9);
    expect(fontLoads).toContain('400 100px "JetBrains Mono"');
    expect(state.fontUrls).toEqual([
      "/assets/fonts/ArchivoBlack.ttf",
      "/assets/fonts/Anton.ttf",
      "/assets/fonts/BlackHanSans.ttf",
    ]);
    expect(E.layers).toHaveLength(1);
    expect(hud.load).toHaveBeenCalledWith(E, E.layers[0]);
    expect(E.layers[0]).toMatchObject({ id: "hud", z: 100, loaded: true });
  });

  const TIMELINE = [
    { id: "a", start: 0, end: 2 },
    { id: "a_v", start: 0, end: 2, canvas: "portrait" },
    { id: "end", file: "end_a.js", start: 2, end: 4, variant: "a" },
    { id: "end_b", start: 2, end: 4, variant: "b" },
    { id: "hud", start: 0, end: 99, z: 100 },
  ];
  const files = ["a.js", "a_v.js", "end_a.js", "end_b.js", "hud.js"];
  const scenes = () =>
    Object.fromEntries(files.map((f) => [f, { render: () => 1 }]));
  const ids = (p: Page) => p.E.layers.map((l: Layer) => l.id);

  it.each([
    ["", ["a", "end", "hud"]],
    ["?variant=b", ["a", "end_b", "hud"]],
    ["?ending=b", ["a", "end_b", "hud"]],
    ["?canvas=portrait", ["a", "a_v", "end", "hud"]],
    ["?only=end,end_b", ["end", "end_b"]],
    ["?only=a,a_v", ["a"]],
  ])("picks the layers for %j", async (search, expected) => {
    const page = await boot({
      search,
      timeline: { TIMELINE },
      scenes: scenes(),
    });
    expect(page.win.__error).toBeUndefined();
    expect(ids(page)).toEqual(expected);
  });

  it("loads a layer's scene from its file when it names one", async () => {
    const s = scenes();
    const page = await boot({ timeline: { TIMELINE }, scenes: s });
    const end = page.E.layers.find((l: Layer) => l.id === "end");
    expect(end.scene).toBe(s["end_a.js"]);
  });

  it("fails an --only that leaves nothing on this canvas", async () => {
    const page = await boot({
      search: "?only=a_v",
      timeline: { TIMELINE },
      scenes: scenes(),
    });
    expect(page.win.__error).toContain(
      "--only a_v: nothing renders on the landscape canvas",
    );
    expect(page.win.__ready).toBeUndefined();
  });
});

describe("renderTime", () => {
  const twoLayers = (log: string[], back: Partial<Scene> = {}) => ({
    timeline: {
      TIMELINE: [
        { id: "front", start: 1, end: 3, z: 5 },
        { id: "back", start: 0, end: 2, z: 0, blend: "add" },
      ],
    },
    scenes: {
      "front.js": scene(log, "front"),
      "back.js": { ...scene(log, "back", 0.5), ...back },
    },
  });

  it("prepares every active layer, then composites them from back to front", async () => {
    const log: string[] = [];
    const { win, E } = await boot(twoLayers(log));
    const r = state.renderers[0];
    await win.renderTime(1.5);
    expect(log).toEqual([
      "prepare:back@1.5",
      "prepare:front@1.5",
      "render:back@1.5",
      "render:front@1.5",
    ]);
    expect([E.t, E.frame]).toEqual([1.5, 90]);
    const [back, front] = r.composites;
    expect(r.composites).toHaveLength(2);
    expect(back).toMatchObject({
      opacity: 0.5,
      blendSrc: "OneFactor",
      blendDst: "OneFactor",
    });
    expect(front).toMatchObject({
      opacity: 1,
      blendSrc: "OneFactor",
      blendDst: "OneMinusSrcAlphaFactor",
    });
    expect(back.target).toBe(front.target);
    expect((back.tex as any).target).not.toBe((front.tex as any).target);
    expect(r.calls).toContainEqual(["setClearColor", 0, 1]);
    expect(state.composers[0].renders).toBe(1);
  });

  it("renders a layer from its start up to, not including, its end", async () => {
    const log: string[] = [];
    const { win } = await boot(twoLayers(log));
    await win.renderTime(0.5);
    await win.renderTime(2);
    expect(log.filter((l) => l.startsWith("render"))).toEqual([
      "render:back@0.5",
      "render:front@2",
    ]);
  });

  it("hands each layer its own target and composites what it drew there", async () => {
    const targets: unknown[] = [];
    const log: string[] = [];
    const { win } = await boot(
      twoLayers(log, { render: (_E, _t, rt) => void targets.push(rt) }),
    );
    await win.renderTime(1.5);
    const [back] = state.renderers[0].composites;
    expect((back.tex as any).target).toBe(targets[0]);
    // a scene that returns no number composites at full opacity
    expect(back.opacity).toBe(1);
  });

  it.each([
    ["screen", "OneFactor", "OneMinusSrcColorFactor"],
    ["multiply", "DstColorFactor", "ZeroFactor"],
    ["normal", "OneFactor", "OneMinusSrcAlphaFactor"],
  ])("blends a %s layer", async (blend, src, dst) => {
    const { win } = await boot({
      timeline: { TIMELINE: [{ id: "x", start: 0, end: 9, blend }] },
      scenes: { "x.js": { render: () => 1 } },
    });
    await win.renderTime(1);
    expect(state.renderers[0].composites[0]).toMatchObject({
      blendSrc: src,
      blendDst: dst,
    });
  });
});

describe("post", () => {
  const withScene = (render: Scene["render"], timeline = {}) =>
    boot({
      timeline: { TIMELINE: [{ id: "x", start: 0, end: 9 }], ...timeline },
      scenes: { "x.js": { render } },
    });

  it("maps a scene's post settings onto the final pass for that frame only", async () => {
    let frame = 0;
    const seen: unknown[] = [];
    const { win } = await withScene((E) => {
      seen.push([E.post.grade, E.post.tint[0], E.hud.alpha]);
      if (frame++ > 0) return;
      Object.assign(E.post, {
        bloom: 1.2,
        flash: 0.01,
        grade: "warm",
        invertCol: "#00FF00",
        shake: [0.01, -0.02],
        fade: 0.5,
      });
      E.post.tint[0] = 0.25;
      E.hud.alpha = 0;
    });
    await win.renderTime(1);
    const U = finalUniforms();
    expect(bloom().strength).toBe(1.2);
    expect(U.uFlash.value).toBe(0);
    expect(U.uWarm.value).toBe(1);
    expect(U.uAmber.value.value).toBe("#00FF00");
    expect([U.uShake.value.x, U.uShake.value.y]).toEqual([0.01, -0.02]);
    expect(U.uTint.value.x).toBe(0.25);
    expect(U.uFade.value).toBe(0.5);

    await win.renderTime(2);
    expect(seen[1]).toEqual(["neutral", 1, 1]);
    expect(bloom().strength).toBe(0.55);
    expect(U.uWarm.value).toBe(0);
    expect(U.uTint.value.x).toBe(1);
    expect(U.uFade.value).toBe(1);
  });

  it("passes a flash through once it clears the threshold", async () => {
    const { win } = await withScene((E) => {
      E.post.flash = 0.5;
      E.post.flashCol = [1, 0, 0];
    });
    await win.renderTime(1);
    const U = finalUniforms();
    expect(U.uFlash.value).toBe(0.5);
    expect([U.uFlashCol.value.r, U.uFlashCol.value.g]).toEqual([1, 0]);
  });

  it("starts every frame from timeline.js POST merged over the neutral defaults", async () => {
    const { win } = await withScene(() => 1, {
      POST: { grain: 0.04, grade: "warm" },
    });
    await win.renderTime(1);
    const U = finalUniforms();
    expect(U.uGrain.value).toBe(0.04);
    expect(U.uWarm.value).toBe(1);
    expect(U.uVig.value).toBe(0);
    expect(bloom().threshold).toBe(1.05);
  });
});

describe("page API", () => {
  const one = {
    timeline: { TIMELINE: [{ id: "x", start: 0, end: 9 }] },
    scenes: { "x.js": { render: () => 1 } },
  };

  it("renders a frame index at the requested fps and keeps that fps", async () => {
    const { win, E } = await boot(one);
    expect(await win.renderFrame(45, 30)).toBe(true);
    expect([E.fps, E.t, E.frame]).toEqual([30, 1.5, 45]);
    expect(finalUniforms().uFrame.value).toBe(45);
    await win.renderTime(2);
    expect(E.frame).toBe(60);
  });

  it("grabs the canvas as encoded bytes", async () => {
    const { win, canvas } = await boot(one);
    expect(Array.from(await win.grab())).toEqual([7, 8, 9]);
    expect(canvas.blobArgs).toEqual(["image/jpeg", 0.93]);
    await win.grab("image/png", 1);
    expect(canvas.blobArgs).toEqual(["image/png", 1]);
  });

  it("renders the ?t still once booted", async () => {
    const { E } = await boot({ ...one, search: "?t=1.25" });
    await vi.waitFor(() => expect(state.composers[0].renders).toBe(1));
    expect(E.t).toBe(1.25);
  });

  it("plays from ?play in real time, one frame per animation frame", async () => {
    // a settable clock, since the test runner may read performance.now too
    let clock = 1000;
    vi.spyOn(performance, "now").mockImplementation(() => clock);
    const { E, frameCallbacks } = await boot({ ...one, search: "?play=2" });
    await vi.waitFor(() => expect(frameCallbacks).toHaveLength(1));
    expect(E.t).toBe(2);
    clock = 1500;
    await frameCallbacks[0]();
    await vi.waitFor(() => expect(frameCallbacks).toHaveLength(2));
    expect(E.t).toBe(2.5);
  });
});
