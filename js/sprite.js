// sprite.js — plays one sprite sheet described by the manifest.
// A sheet is a single row of equal frames. The sprite knows nothing about
// where it is in the scene; callers pass a position and it draws the frame
// with its anchor on that position.
// Exports: createSprite(animation)
//   -> { width, height, durationMs, frameAt, isFinished, draw, contains }
//          drawnBoxes(animation) -> per frame, the box around its opaque pixels

export function createSprite(animation) {
  const { info, imageFor } = animation;
  const [anchorX, anchorY] = info.anchor;

  // Which frame to show after `elapsedMs` of playing. A one-shot animation
  // returns -1 once it has played through.
  function frameAt(elapsedMs) {
    if (info.frames <= 1 || info.ms_per_frame <= 0) return 0;
    const step = Math.floor(elapsedMs / info.ms_per_frame);
    if (info.loop) return step % info.frames;
    return step < info.frames ? step : -1;
  }

  function isFinished(elapsedMs) {
    return frameAt(elapsedMs) === -1;
  }

  // Draws `frame` with the anchor pixel at (x, y). When mirrored, the sprite
  // flips around the anchor pixel, so a flipped sprite stays on the same spot.
  // Returns false if this sheet has no version for `time` (e.g. stars by day).
  function draw(ctx, time, frame, x, y, mirrored = false) {
    const image = imageFor(time);
    if (!image || frame < 0) return false;
    const w = info.frame_w, h = info.frame_h;
    const sourceX = frame * w;
    if (!mirrored) {
      ctx.drawImage(image, sourceX, 0, w, h, x - anchorX, y - anchorY, w, h);
      return true;
    }
    ctx.save();
    ctx.translate(x + anchorX + 1, y - anchorY);
    ctx.scale(-1, 1);
    ctx.drawImage(image, sourceX, 0, w, h, 0, 0, w, h);
    ctx.restore();
    return true;
  }

  // Whether art pixel (px, py) is on the frame drawn with its anchor at
  // (x, y), give or take `padding` pixels: a forgiving box for clicks.
  function contains(px, py, x, y, mirrored = false, padding = 0) {
    const left = mirrored ? x - (info.frame_w - 1 - anchorX) : x - anchorX;
    const top = y - anchorY;
    return px >= left - padding && px < left + info.frame_w + padding
      && py >= top - padding && py < top + info.frame_h + padding;
  }

  return {
    width: info.frame_w,
    height: info.frame_h,
    durationMs: info.frames * info.ms_per_frame,   // one play-through
    frameAt,
    isFinished,
    draw,
    contains,
  };
}

// For each frame, { x, y, w, h } around its opaque pixels (relative to the
// frame's top-left), or null for an empty frame. The shape is the same at
// every time of day, so the day sheet stands for all.
export function drawnBoxes(animation) {
  const { frame_w: w, frame_h: h, frames } = animation.info;
  const canvas = document.createElement('canvas');
  canvas.width = w * frames;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(animation.imageFor('day'), 0, 0);
  const alpha = ctx.getImageData(0, 0, w * frames, h).data;
  const boxes = [];
  for (let f = 0; f < frames; f++) {
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        if (alpha[(y * w * frames + f * w + x) * 4 + 3] === 0) continue;
        x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y);
      }
    }
    boxes.push(x1 < 0 ? null : { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 });
  }
  return boxes;
}
