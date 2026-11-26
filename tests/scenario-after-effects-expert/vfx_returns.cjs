// vfx_returns.cjs: offline check of what each builder in vfx.jsx returns, run without After Effects
// (node vfx_returns.cjs [vfx.jsx]). test_effects_offline.py runs it in the family suite.
// It loads vfx.jsx (or the copy named as its argument) against a stand-in for the AEK kit and the After Effects object model, calls each builder, and checks two things:
// the keys of the result match the "Returns {...}" line of the builder's comment, and each key holds what SPEC says
// (name: a string; object: a layer, comp or effect; names: an array of strings; other: anything else).
// Exit code 1 on any mismatch.
"use strict";
const fs = require("fs"),
  path = require("path"),
  vm = require("vm");

// A stand-in object: any property is another stand-in, any call returns one, it reads as 1 in arithmetic and as its name in text.
function M(name, ext) {
  const store = Object.assign({ name: String(name) }, ext || {});
  const target = function () {};
  return new Proxy(target, {
    get(t, p) {
      if (p === Symbol.toPrimitive) {
        return (hint) => (hint === "string" ? store.name : 1);
      }
      if (p === "__isMock") {
        return true;
      }
      if (Object.prototype.hasOwnProperty.call(store, p)) {
        return store[p];
      }
      if (p === "toString") {
        return () => store.name;
      }
      if (p === "valueOf") {
        return () => 1;
      }
      if (p === "then" || typeof p === "symbol") {
        return undefined;
      }
      if (p === "numProperties" || p === "numKeys") {
        return 0;
      }
      const child = M(String(p));
      store[p] = child;
      return child;
    },
    set(t, p, v) {
      store[p] = v;
      return true;
    },
    apply() {
      return M("value");
    },
    construct() {
      return M("new");
    },
  });
}
function layer(name, ext) {
  return M(
    name,
    Object.assign({ index: 1, width: 1920, height: 1080 }, ext || {}),
  );
}
function comp(name, o) {
  o = o || {};
  const c = M(name, {
    width: o.width || 1920,
    height: o.height || 1080,
    frameRate: o.fps || 30,
    duration: o.duration || 4,
    numLayers: o.numLayers === undefined ? 3 : o.numLayers,
    frameDuration: 1 / 30,
  });
  c.layers = M("layers", {
    add: (item) =>
      layer(item && item.name ? item.name : "layer", { source: item }),
    addShape: () => layer("Shape Layer"),
    addNull: () => layer("Null"),
    addSolid: () => layer("Solid"),
    addText: () => layer("Text"),
  });
  c.layer = (n) => layer(typeof n === "string" ? n : "L" + n);
  return c;
}
const comps = {};
// files that exist on the stand-in disk, the frames captured, the files written
const failWrite = new Set(),
  failCapture = new Set(),
  disk = new Set(),
  captured = [],
  written = {};
const AEK = {
  core: {
    comp: (n) => comps[n] || comp(n),
    layer: (c, n) => layer(typeof n === "string" ? n : "L" + n),
    item: (n) =>
      M(n, { width: 1920, height: 1080, frameRate: 30, duration: 5 }),
    abs: (p) => new sandbox.File(p),
    ensureFolder: () => {},
    frame: (c, s) => Math.round(s * 30),
    log: () => {},
  },
  build: {
    // like the kit: a name in use throws unless reuse; a new comp starts empty
    comp: (n, o) => {
      if (comps[n]) {
        if (o && o.reuse) {
          return comps[n];
        }
        throw new Error("A comp named '" + n + "' already exists");
      }
      comps[n] = comp(n, Object.assign({ numLayers: 0 }, o));
      comps[n].remove = () => {
        delete comps[n];
      };
      return comps[n];
    },
    solid: (c, n) => layer(n),
    adjustment: (c, n) => layer(n),
    nullLayer: (c, n) => layer(n),
    shape: (c, n) => layer(n),
    shapeGroup: (l, s) => M(s && s.name ? s.name : "group"),
    effect: (l, mn, p, n) => M(n || mn),
    effectProps: () => [],
    parent: () => {},
    matte: () => {},
    precompose: (c, i, n) => comp(n),
    anchor: () => {},
    camera: (c, n) => layer(n),
  },
  xio: {
    importItem: (p) =>
      M("footage", { width: 1920, height: 1080, frameRate: 30, duration: 5 }),
    addToComp: (c, it, o) => layer((o && o.name) || "PLATE"),
    describe: () => ({}),
  },
  capture: {
    frame: (c, s, p) => {
      if (failCapture.has(p)) {
        throw new Error("Frame not written: " + p);
      }
      captured.push({ comp: String(c.name), time: s, path: p });
      disk.add(p);
      return { path: p, time: s, frame: Math.round(s * 30), pngScale: 1 };
    },
    frames: () => [],
    timeoutMs: 1000,
  },
  motion: { bezier: () => {}, ease: () => {}, key: () => {} },
  expr: { set: () => {} },
  json: { stringify: (v) => JSON.stringify(v), parse: (t) => JSON.parse(t) },
  log: () => {},
};
AEK.log = () => {};
const sandbox = {
  AEK,
  Math,
  Date,
  Error,
  parseInt,
  parseFloat,
  String,
  Number,
  Array,
  Object,
  isNaN,
  app: M("app", {
    project: M("project", { bitsPerChannel: 16, colorManagementSystem: 0 }),
  }),
  BlendingMode: M("BlendingMode"),
  TrackMatteType: M("TrackMatteType"),
  MaskMode: M("MaskMode"),
  KeyframeInterpolationType: M("KIT"),
  Shape: function () {},
  CompItem: function () {},
  FootageItem: function () {},
  File: function (p) {
    return {
      fsName: p,
      encoding: "",
      open() {
        return !failWrite.has(p);
      },
      write(t) {
        written[p] = t;
        disk.add(p);
        return true;
      },
      close() {
        return true;
      },
      remove() {
        disk.delete(p);
        delete written[p];
        return true;
      },
      get exists() {
        return disk.has(p);
      },
      parent: { fsName: path.dirname(p) },
    };
  },
  $: { sleep() {} },
};
vm.createContext(sandbox);
const SRC = fs.readFileSync(
  process.argv[2] ||
    path.join(
      __dirname,
      "..",
      "..",
      "skills",
      "dcc",
      "after-effects",
      "scenario-after-effects-vfx",
      "scripts",
      "vfx.jsx",
    ),
  "utf8",
); // optional: another copy of vfx.jsx
vm.runInContext(SRC + "\nthis.AEX = AEX;", sandbox);
const AEX = sandbox.AEX;

// documented keys: the "Returns {a, b, c}" of the comment block just above "function <fn>(" inside "AEX.<mod> = (function".
function docKeys(mod, fn) {
  const start = SRC.indexOf("AEX." + mod + " = (function");
  const end = SRC.indexOf("\nAEX.", start + 10);
  const body = SRC.slice(start, end < 0 ? undefined : end);
  const at = body.search(new RegExp("\\n\\s*function " + fn + "\\("));
  if (at < 0) {
    return null;
  }
  const lines = body.slice(0, at).split("\n");
  let txt = "";
  for (let i = lines.length - 1; i >= 0 && /^\s*\/\//.test(lines[i]); i--) {
    txt = lines[i] + " " + txt;
  }
  const m = txt.match(/Returns \{([^}]*)\}([^.]*)/);
  if (!m) {
    return null;
  }
  const keys = m[1]
    .split(",")
    .map((s) => s.trim().split(" ")[0])
    .filter(Boolean)
    .sort();
  keys.saysNames =
    /\bnames\b/.test(m[2]) ||
    /\bare names\b/.test(txt) ||
    /\(names[,;:)]/.test(txt) ||
    /layer names/.test(txt);
  return keys;
}
function kind(v) {
  if (typeof v === "string") {
    return "name";
  }
  if (v && v.__isMock) {
    return "object";
  }
  if (Array.isArray(v)) {
    return v.every((x) => typeof x === "string") ? "names" : "other";
  }
  return "other";
}
sandbox.host = () => {
  delete comps.HOST;
  return AEK.build.comp("HOST", {
    width: 1920,
    height: 1080,
    fps: 30,
    duration: 4,
    numLayers: 3,
  });
};
sandbox.plateItem = M("plate", {
  width: 1920,
  height: 1080,
  frameRate: 30,
  duration: 5,
});
// SPEC: module, function, call, expected kind per key (keys not listed: other). Names for what a job returns as JSON; objects where noted.
const SPEC = [
  [
    "light",
    "rig",
    'AEX.light.rig(host(), "RIG", {})',
    { light: "object", sum: "object", layer: "object" },
  ],
  [
    "burst",
    "build",
    'AEX.burst.build(host(), { name: "BURST", center: [960, 540], at: 0.5 })',
    {
      name: "name",
      light: "name",
      layer: "name",
      air: "name",
      streaks: "name",
      sparks: "name",
      core: "names",
    },
  ],
  [
    "burst",
    "planes",
    'AEX.burst.planes(host(), { name: "PLANES", center: [960, 540], at: 0.5 })',
    { comp: "name", layer: "name", glow: "name" },
  ],
  [
    "atmo",
    "build",
    'AEX.atmo.build(host(), { name: "ATMO", L: 4, beam: [1300, 260, 900, 900], title: [960, 500, 520, 160] })',
    { comps: "names", layer: "name" },
  ],
  [
    "motes",
    "build",
    'AEX.motes.build(host(), { name: "MOTES", L: 4, beam: [620, 360, 1180, 760] })',
    { comps: "names", layer: "name", beam: "name" },
  ],
  [
    "smoke",
    "build",
    'AEX.smoke.build(host(), { name: "SMOKE", L: 4, center: [960, 600], size: [520, 380] })',
    { comps: "names", layers: "names", layer: "name", grey: "name" },
  ],
  [
    "smoke",
    "flame",
    'AEX.smoke.flame(host(), { name: "FLAME", base: [960, 940], height: 680, L: 4 })',
    {
      name: "name",
      flame: "name",
      embers: "name",
      heat: "name",
      light: "name",
      layer: "name",
    },
  ],
  [
    "plume",
    "build",
    'AEX.plume.build(host(), { name: "PLUME", base: [960, 900], L: 4 })',
    { name: "name", layer: "name", grey: "name" },
  ],
  [
    "element",
    "land",
    'AEX.element.land(host(), plateItem, { name: "FIRE", base: [960, 940], foot: 1000 })',
    {
      layer: "name",
      glow: "name",
      pool: "name",
      lift: "name",
      warnings: "other",
    },
  ],
  [
    "shock",
    "stroke",
    "AEX.shock.stroke(host(), { center: [960, 540] })",
    { edge: "object", wake: "object" },
  ],
  [
    "shock",
    "polar",
    "AEX.shock.polar(host(), { center: [960, 540] })",
    { layer: "object", band: "object" },
  ],
  [
    "shock",
    "refraction",
    "AEX.shock.refraction(host(), { center: [960, 540] })",
    { layer: "object", maps: "other" },
  ],
  [
    "integrate",
    "build",
    "AEX.integrate.build(host(), plateItem, { burst: { center: [960, 540] }, floorY: 800, black: [0.02, 0.02, 0.03] })",
    { layers: "names", envelope: "other", warnings: "other" },
  ],
  [
    "distort",
    "apply",
    "AEX.distort.apply(host(), plateItem, { haze: { region: [600, 200, 1300, 700], amount: 6 } })",
    { layers: "names", maps: "names", warnings: "other" },
  ],
  [
    "pulse",
    "build",
    'AEX.pulse.build(plateItem, { name: "PULSE", dur: 4 })',
    {
      scene: "object",
      cam: "object",
      finalComp: "object",
      layers: "names",
      rig: "names",
      warnings: "other",
    },
  ],
];
let bad = 0;
for (const [mod, fn, call, spec] of SPEC) {
  let r;
  try {
    r = vm.runInContext(call, sandbox, { timeout: 10000 });
  } catch (e) {
    console.log("FAIL", mod + "." + fn, "threw", e.message);
    bad++;
    continue;
  }
  const got = Object.keys(r).sort(),
    doc = docKeys(mod, fn),
    errs = [];
  if (!doc) {
    errs.push("no 'Returns {...}' in its comment");
  } else {
    const missing = doc.filter((k) => !(k in r)),
      extra = got.filter((k) => doc.indexOf(k) < 0);
    if (missing.length) {
      errs.push("documented but not returned: " + missing.join(", "));
    }
    if (extra.length) {
      errs.push("returned but not documented: " + extra.join(", "));
    }
  }
  const nameKeys = Object.keys(spec).filter(
    (k) => spec[k] === "name" || spec[k] === "names",
  );
  if (doc && nameKeys.length && !doc.saysNames) {
    errs.push(
      "returns names (" +
        nameKeys.join(", ") +
        ") but its comment does not say 'names'",
    );
  }
  for (const k of Object.keys(spec)) {
    const v = r[k];
    if (v === null || v === undefined) {
      continue;
    } // optional parts switched off
    if (kind(v) !== spec[k] && spec[k] !== "other") {
      errs.push(k + " is " + kind(v) + ", SPEC says " + spec[k]);
    }
  }
  console.log(errs.length ? "FAIL" : "ok  ", mod + "." + fn, errs.join("; "));
  bad += errs.length ? 1 : 0;
}

// Pure-logic checks: each names the defect it guards against.
function check(label, fn) {
  let err = null;
  try {
    err = fn();
  } catch (e) {
    err = "threw " + e.message;
  }
  console.log(err ? "FAIL" : "ok  ", label, err || "");
  bad += err ? 1 : 0;
}
const run = (code) => vm.runInContext(code, sandbox, { timeout: 10000 });
check("vfx.cost: frame numbers padded, never truncated", () => {
  const c = comp("COST");
  const f = run("AEX.vfx.cost")(c, [0, 1000 / 30], "/d", "p");
  const a = f[0].path,
    b = f[1].path;
  return a === "/d/p_f000.png" && b === "/d/p_f1000.png"
    ? null
    : "paths " + a + ", " + b;
});
check("vfxu.lit: a name with quotes and backslashes reads back whole", () => {
  const name = 'Null "A" \\ 2';
  const l = run("AEX.vfxu.lit")(name);
  if (eval(l) !== name) {
    return "literal " + l;
  }
  const ex = run("AEX.vfx.followExpr")(name, "x");
  return ex.indexOf("thisComp.layer(" + l + ")") >= 0 ? null : "follow " + ex;
});
check("glow.gain: copies made with a prefix are found by the prefix", () => {
  const c = comp("GAIN"),
    asked = [];
  c.layer = (n) => {
    asked.push(n);
    return layer(n);
  };
  run("AEX.glow.gain")(c, "SRC", 2, { prefix: "PFX", n: 2 });
  return asked.join() === "PFX glow 12,PFX glow 24" ? null : asked.join();
});
check(
  "pulse.build: all embers in BACK leaves an empty FRONT plane (terminates)",
  () => {
    const r = run(
      'AEX.pulse.build(plateItem, { name: "EMB", dur: 4, embers: 10, emberBack: 1 })',
    );
    const e = r.embers;
    return e.count[0] === 0 && e.count[1] === 10 && e.sizes.length === 10
      ? null
      : JSON.stringify(e);
  },
);
let G = null;
check(
  "pulse.gateFrames: every flash frame, hold on the camera comp, pngScale",
  () => {
    G = run('AEX.pulse.build(plateItem, { name: "GATE", dur: 4 })');
    sandbox.G = G;
    const m = run('AEX.pulse.gateFrames(G, "/g1")');
    const fr = m.peaks.map((p) => Number(p.match(/_(\d+)\.png$/)[1]));
    for (let i = 1; i < fr.length; i++) {
      if (fr[i] !== fr[i - 1] + 1) {
        return "flash frames " + fr.join();
      }
    }
    if (fr.length !== 16) {
      return "flash frames " + fr.length;
    }
    const holdComps = captured
      .filter((c) => /_hold_/.test(c.path))
      .map((c) => c.comp);
    if (!m.holdFrames.length || m.holdFrames.length !== m.holdCount) {
      return "hold frames " + m.holdFrames.length + " of " + m.holdCount;
    }
    if (holdComps.some((n) => n !== "GATE_CAM")) {
      return "hold from " + holdComps.join();
    }
    if (comps.GATE_PLATEONLY) {
      return "plate-only comp left in the project";
    }
    const j = JSON.parse(written["/g1/manifest.json"]);
    return j.pngScale === 1 &&
      j.version === 2 &&
      m.manifest === "/g1/manifest.json"
      ? null
      : "manifest " + written["/g1/manifest.json"];
  },
);
check(
  "pulse.gateFrames: an existing frame or manifest stops it before any write",
  () => {
    const n = captured.length;
    try {
      run('AEX.pulse.gateFrames(G, "/g1")');
    } catch (e) {
      return /already exist/.test(e.message) && captured.length === n
        ? null
        : e.message;
    }
    return "no error on a second run into the same folder";
  },
);
check("pulse.gateFrames: late time past the end is refused", () => {
  try {
    run('AEX.pulse.gateFrames(G, "/g2", { late: [0.5, 9] })');
  } catch (e) {
    return /late/.test(e.message) && !disk.has("/g2/manifest.json")
      ? null
      : e.message;
  }
  return "no error";
});
check(
  "pulse.gateFrames: an existing plate-only comp is kept, the temporary one removed",
  () => {
    const mine = comp("GATE_PLATEONLY");
    comps.GATE_PLATEONLY = mine;
    run('AEX.pulse.gateFrames(G, "/g3")');
    return comps.GATE_PLATEONLY === mine && !comps.GATE_PLATEONLY_2
      ? null
      : Object.keys(comps).join();
  },
);
check(
  "pulse.gateFrames: a failed capture still removes the temporary comp",
  () => {
    failCapture.add("/g4/g_hold_119.png");
    try {
      run('AEX.pulse.gateFrames(G, "/g4")');
    } catch (e) {
      return !comps.GATE_PLATEONLY_2 && !disk.has("/g4/manifest.json")
        ? null
        : "comp or manifest left after: " + e.message;
    }
    return "no error";
  },
);
check(
  "pulse.gateFrames: a failed manifest write throws and leaves no manifest",
  () => {
    failWrite.add("/g5/manifest.json");
    try {
      run('AEX.pulse.gateFrames(G, "/g5")');
    } catch (e) {
      return /manifest not written/.test(e.message) &&
        !disk.has("/g5/manifest.json")
        ? null
        : e.message;
    }
    return "no error";
  },
);
console.log(
  bad
    ? bad + " builder(s) do not match"
    : "all builders match their documented returns, all logic checks pass",
);
process.exit(bad ? 1 : 0);
