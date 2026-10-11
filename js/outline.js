// outline.js — the hover highlight for clickable sill items: a one-pixel
// outline around the opaque pixels of a sprite's first frame.
// Exports: createOutline(animation, colour, { steadyOnly }) -> { image, covers(x, y) }
//   steadyOnly: outline only the pixels that are fully opaque in every
//   frame, so moving see-through parts (the mug's steam) are left out.
//   image is one pixel bigger than the sprite on every side; draw it at
//   (sprite left - 1, sprite top - 1). covers(x, y) tells whether a point,
//   relative to the sprite's top-left, is on the sprite or its outline.

export function createOutline(animation, colour, { steadyOnly = false } = {}) {
  const { frame_w: width, frame_h: height, frames } = animation.info;
  // Every time-of-day version has the same shape, so one outline serves all.
  const source = animation.imageFor('day');
  const w = width + 2, h = height + 2;
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const alphaOf = (frame) => {
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(source, frame * width, 0, width, height, 1, 1, width, height);
    return ctx.getImageData(0, 0, w, h).data;
  };
  const shape = new Uint8Array(w * h);
  const first = alphaOf(0);
  for (let i = 0; i < w * h; i++) shape[i] = steadyOnly ? first[i * 4 + 3] === 255 : first[i * 4 + 3] > 0;
  for (let frame = 1; steadyOnly && frame < frames; frame++) {
    const alpha = alphaOf(frame);
    for (let i = 0; i < w * h; i++) shape[i] &&= alpha[i * 4 + 3] === 255;
  }
  const solid = (x, y) => x >= 0 && y >= 0 && x < w && y < h && shape[y * w + x];

  const covered = new Set();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = colour;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const nextToSolid = solid(x - 1, y) || solid(x + 1, y) || solid(x, y - 1) || solid(x, y + 1);
      if (solid(x, y)) covered.add(y * w + x);
      else if (nextToSolid) { covered.add(y * w + x); ctx.fillRect(x, y, 1, 1); }
    }
  }
  return {
    image: canvas,
    covers: (x, y) => covered.has((y + 1) * w + (x + 1)) && x >= -1 && y >= -1 && x <= width && y <= height,
  };
}
