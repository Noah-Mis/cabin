// precipitation.js — rain or snow, a seamless tile repeated over the canvas.
// Which one (if any) comes from the weather module.
// Exports: createPrecipitation(assets, weather) -> scene element

import { createSprite } from '../sprite.js';

export function createPrecipitation(assets, weather) {
  const [width, height] = assets.manifest.canvas;
  // Weather names that have a sheet of the same name in the manifest.
  const sprites = {
    rain: createSprite(assets.animation('rain')),
    snow: createSprite(assets.animation('snow')),
  };
  let elapsedMs = 0;

  return {
    update(dtMs) { elapsedMs += dtMs; },
    draw(ctx, time) {
      const sprite = sprites[weather.get()];
      if (!sprite) return;   // clear skies
      const frame = sprite.frameAt(elapsedMs);
      for (let y = 0; y < height; y += sprite.height) {
        for (let x = 0; x < width; x += sprite.width) sprite.draw(ctx, time, frame, x, y);
      }
    },
  };
}
