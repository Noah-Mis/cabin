// waterfall.js — the flowing-water patch over the falls, always running,
// with the quiet sound of the falls looping underneath.
// Exports: createWaterfall(assets) -> scene element

import { createSprite } from '../sprite.js';
import { loop } from '../sound.js';

export function createWaterfall(assets) {
  const animation = assets.animation('waterfall');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  let elapsedMs = 0;
  loop('waterfall');

  return {
    update(dtMs) { elapsedMs += dtMs; },
    draw(ctx, time) { sprite.draw(ctx, time, sprite.frameAt(elapsedMs), x, y); },
  };
}
