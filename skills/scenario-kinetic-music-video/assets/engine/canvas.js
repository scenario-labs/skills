// Canvas size, orientation and safe band, at scale 1 (main.js multiplies by SCALE).
// A project renders at the CANVAS in timeline.js; ?canvas= (render.mjs/still.mjs --canvas) overrides it for a second ratio.
export const PRESETS = {
  landscape: [1920, 1080],
  portrait: [1080, 1920],
  square: [1080, 1080],
};

// Platform UI covers the edges of a 9:16 feed: top bar, caption and buttons at the bottom, an action rail on the right.
// Fractions of the canvas, authoring-time values (the band scenario-formats and scenario-video-ads compose to).
export const TALL_SAFE = { top: 0.14, bottom: 0.35, left: 0.06, right: 0.13 };
const FULL = { top: 0, bottom: 0, left: 0, right: 0 };

// 'portrait' | 'landscape' | 'square' | 'WxH' | [w, h] -> [w, h], or null. Sides must be even (H.264 4:2:0 refuses odd ones).
export function parseCanvas(v) {
  let w, h;
  if (Array.isArray(v)) [w, h] = v;
  else {
    const s = String(v ?? "")
      .trim()
      .toLowerCase();
    if (PRESETS[s]) return [...PRESETS[s]];
    const m = s.match(/^(\d+)x(\d+)$/);
    if (!m) return null;
    [w, h] = [+m[1], +m[2]];
  }
  const ok = (n) => Number.isInteger(n) && n >= 2 && n % 2 === 0;
  return ok(w) && ok(h) ? [w, h] : null;
}

// The query value wins over timeline.js CANVAS; landscape when neither is set. Throws on a value it cannot read.
export function resolveCanvas(query, timelineCanvas) {
  for (const v of [query, timelineCanvas]) {
    if (v == null || v === "") continue;
    const c = parseCanvas(v);
    if (!c)
      throw new Error(
        `canvas ${JSON.stringify(v)}: use landscape, portrait, square or WxH with even sides`,
      );
    return c;
  }
  return [...PRESETS.landscape];
}

export function orientation(w, h) {
  return w === h ? "square" : h > w ? "portrait" : "landscape";
}

// Insets for this canvas. timeline.js SAFE overrides per orientation, e.g. { landscape: { top: 0.1, bottom: 0.1 } }.
// Without one, a 9:16-tall canvas gets TALL_SAFE and anything wider keeps the full frame.
export function safeInsets(w, h, overrides) {
  const o = overrides?.[orientation(w, h)];
  if (o) return { ...FULL, ...o };
  return h / w >= 1.7 ? { ...TALL_SAFE } : { ...FULL };
}

// Safe band in pixels of a W x H canvas.
export function safeRect(W, H, insets) {
  return {
    x: Math.round(W * insets.left),
    y: Math.round(H * insets.top),
    w: Math.round(W * (1 - insets.left - insets.right)),
    h: Math.round(H * (1 - insets.top - insets.bottom)),
  };
}

// Shift a perspective camera's frame so its center lands on the safe band's center: 3D placed at the origin then sits
// clear of platform UI. No-op on a full-frame band, so landscape renders are unchanged.
export function centerOnSafe(cam, W, H, R) {
  const dx = W / 2 - (R.x + R.w / 2),
    dy = H / 2 - (R.y + R.h / 2);
  if (dx || dy) cam.setViewOffset(W, H, dx, dy, W, H);
  return cam;
}

// A TIMELINE entry with `canvas: 'portrait'` (or a list of orientations) renders only on that canvas; without one, on all.
export function onCanvas(entry, orient) {
  return entry.canvas == null || [].concat(entry.canvas).includes(orient);
}
