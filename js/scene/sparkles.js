// sparkles.js — little one-shot twinkles spawned in code: the golden bird's
// trail, a clicked star or bird, the trophy. Not a layer itself: each element
// that sparkles owns a set and draws it in its own place in the stack.
// Exports: createSparkles(assets) -> { spawn(x, y), update(dtMs), draw(ctx, time) }

import { createSprite } from '../sprite.js';

export function createSparkles(assets) {
  const sprite = createSprite(assets.animation('sparkle'));
  let sparkles = [];   // { x, y, elapsedMs }

  return {
    spawn(x, y) { sparkles.push({ x, y, elapsedMs: 0 }); },
    update(dtMs) {
      for (const sparkle of sparkles) sparkle.elapsedMs += dtMs;
      sparkles = sparkles.filter((sparkle) => !sprite.isFinished(sparkle.elapsedMs));
    },
    draw(ctx, time) {
      for (const s of sparkles) sprite.draw(ctx, time, sprite.frameAt(s.elapsedMs), s.x, s.y);
    },
  };
}
