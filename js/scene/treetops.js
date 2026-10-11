// treetops.js — the near-forest tips swaying in the breeze. They sway through
// the sheet once, then rest for a random while (config.treetops). The sheet
// holds only the pixels that change, and frame 0 is empty (trees at rest), so
// resting means drawing nothing.
// Exports: createTreetops(assets) -> scene element

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { randomBetween } from '../random.js';

export function createTreetops(assets) {
  const animation = assets.animation('treetops');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  let swayMs = 0;     // time spent swaying, so each sway starts on frame 0
  let restMs = 0;     // rest left before the next sway

  return {
    update(dtMs) {
      let left = dtMs;
      while (left > 0) {
        if (restMs > 0) {
          const rest = Math.min(left, restMs);
          restMs -= rest;
          left -= rest;
          continue;
        }
        // Sway up to the end of the current cycle, then start a rest.
        const untilCycleEnd = sprite.durationMs - (swayMs % sprite.durationMs);
        const sway = Math.min(left, untilCycleEnd);
        swayMs += sway;
        left -= sway;
        if (sway === untilCycleEnd) restMs = randomBetween(...config.treetops.restBetweenSwaysSec) * 1000;
      }
    },
    draw(ctx, time) {
      if (restMs > 0) return;
      sprite.draw(ctx, time, sprite.frameAt(swayMs), x, y);
    },
  };
}
