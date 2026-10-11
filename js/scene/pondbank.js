// pondbank.js — a strip of grassy bank along the left of the pool, always
// there (scenery, not a reward). Drawn straight after the waterfall, which
// repaints the water every frame, so that the deer stands on land.
// Exports: createPondBank(assets) -> scene element

import { createSprite } from '../sprite.js';

export function createPondBank(assets) {
  const animation = assets.animation('pond_bank');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  return {
    draw(ctx, time) { sprite.draw(ctx, time, 0, x, y); },
  };
}
