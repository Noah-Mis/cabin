// sky.js — a group of elements drawn only where the background is sky.
// Its children draw into a private buffer, which is then cut down to the
// opaque part of sky_mask.png. That is what lets clouds and far birds pass
// behind the mountains and trees.
// Exports: createSky(assets, children) -> scene element with events and pointers

import { config } from '../config.js';

export function createSky(assets, children) {
  const [width, height] = assets.manifest.canvas;
  const buffer = document.createElement('canvas');
  buffer.width = width;
  buffer.height = height;
  const bufferCtx = buffer.getContext('2d');
  bufferCtx.imageSmoothingEnabled = false;
  const mask = assets.image(config.files.skyMask);

  return {
    update(dtMs) {
      for (const child of children) child.update?.(dtMs);
    },
    draw(ctx, time) {
      bufferCtx.clearRect(0, 0, width, height);
      for (const child of children) {
        bufferCtx.save();
        child.draw(bufferCtx, time);
        bufferCtx.restore();
      }
      bufferCtx.globalCompositeOperation = 'destination-in';
      bufferCtx.drawImage(mask, 0, 0);
      bufferCtx.globalCompositeOperation = 'source-over';
      ctx.drawImage(buffer, 0, 0);
    },
    // Pass the children's events and click targets up so they are reachable
    // like any other.
    events: Object.assign({}, ...children.map((child) => child.events ?? {})),
    pointers: children.map((child) => child.pointer).filter(Boolean),
  };
}
