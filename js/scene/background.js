// background.js — the outdoor view (bg_<time>.png), the back of the stack.
// Exports: createBackground(assets) -> scene element

import { config } from '../config.js';

export function createBackground(assets) {
  return {
    draw(ctx, time) {
      ctx.drawImage(assets.timeImage(config.files.background, time), 0, 0);
    },
  };
}
