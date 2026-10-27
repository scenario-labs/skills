import { beforeEach, describe, expect, it, vi } from "vitest";

// core.js and plate.js import three for textures and materials; these tests only reach the clip and tracking logic
vi.mock("three", () => ({
  Texture: class {
    image = null;
  },
  ShaderMaterial: class {
    uniforms: unknown;
    constructor(o: { uniforms: unknown }) {
      this.uniforms = o.uniforms;
    }
  },
  Vector4: class {},
  DoubleSide: 2,
  CustomBlending: 5,
  OneFactor: 201,
  OneMinusSrcAlphaFactor: 205,
  LinearFilter: 1,
  SRGBColorSpace: "srgb",
  NoColorSpace: "",
}));
vi.mock("three/addons/loaders/TTFLoader.js", () => ({ TTFLoader: class {} }));
vi.mock("three/addons/loaders/FontLoader.js", () => ({ Font: class {} }));
vi.mock("three/addons/geometries/TextGeometry.js", () => ({
  TextGeometry: class {},
}));

const { loadVideo, trackFrame } =
  await import("../../skills/scenario-kinetic-music-video/assets/engine/core.js");
const { clock } =
  await import("../../skills/scenario-kinetic-music-video/assets/engine/blur.js");
const { plateMaterialFor } =
  await import("../../skills/scenario-kinetic-music-video/assets/engine/plate.js");

const track = Array.from({ length: 100 }, (_, i) => ({ i }));
globalThis.fetch = (async (u: string) => ({
  json: async () =>
    u.endsWith("meta.json") ? { fps: 30, n: 100, track: true } : track,
  blob: async () => ({}),
})) as unknown as typeof fetch;
globalThis.createImageBitmap = (async () => ({})) as typeof createImageBitmap;

let n = 0;
const clip = async () => loadVideo(`clip_${n++}`);
const idx = (r: { i: number } | null) => r?.i;
// one output frame: the frame pass at t, then a sample at t + shift
function frame(keep: boolean) {
  clock.id++;
  clock.pass++;
  trackFrame(keep);
}
function sample(shift: number) {
  clock.pass++;
  clock.sub = true;
  clock.shift = shift;
}

beforeEach(() => {
  clock.sub = false;
  clock.shift = 0;
  clock.stale = null;
  trackFrame(false);
});

describe("trackAt", () => {
  it("is unchanged without blur, and records nothing", async () => {
    const v = await clip();
    frame(false);
    expect(idx(v.trackAt(2 / 60 + 1 / 30))).toBe(2);
    expect(idx(v.trackAt(1.999))).toBe(59);
    expect(v._seen).toBeUndefined();
  });

  it("returns the frame pass's landmarks inside a sample", async () => {
    const v = await clip();
    const t = 0.33; // clip frame 9, and the sample below reaches clip frame 10
    frame(true);
    expect(idx(v.trackAt(t))).toBe(9);
    sample(0.008);
    expect(idx(v.trackAt(t + 0.008))).toBe(9);
  });

  it("replays slow motion by call order, sample after sample", async () => {
    const v = await clip();
    const t = 1.33; // clip time t / 2 sits just before clip frame 20
    frame(true);
    const want = [-1, 0, 1].map((k) => idx(v.trackAt(t / 2 + k / 30)));
    for (const s of [0.004, 0.008]) {
      sample(s);
      expect(
        [-1, 0, 1].map((k) => idx(v.trackAt((t + s) / 2 + k / 30))),
      ).toEqual(want);
    }
  });

  it("forgets the last frame's calls at the next frame pass", async () => {
    const v = await clip();
    frame(true);
    v.trackAt(1);
    expect(v._seen).toHaveLength(1);
    clock.sub = false;
    frame(false);
    expect(v._seen).toEqual([]);
    sample(0.004);
    expect(idx(v.trackAt(1.5))).toBe(45); // nothing recorded: computed from the time given
  });
});

describe("stale clips", () => {
  it("flags a moving clip a sample draws without prepare() advancing it this frame", async () => {
    const a = await clip(),
      b = await clip();
    frame(true);
    await a.frame(1);
    const ma = plateMaterialFor(a),
      mb = plateMaterialFor(b);
    ma.onBeforeRender();
    mb.onBeforeRender();
    expect(clock.stale).toBeNull(); // the frame pass is never checked
    sample(0.004);
    ma.onBeforeRender();
    expect(clock.stale).toBeNull();
    mb.onBeforeRender();
    expect(clock.stale).toBe(b.name);
  });

  it("never flags a one-frame still", async () => {
    const v = await clip();
    v.meta.n = 1;
    frame(true);
    sample(0.004);
    plateMaterialFor(v).onBeforeRender();
    expect(clock.stale).toBeNull();
  });
});
