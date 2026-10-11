// nearforest.js — the front row of trees, drawn over the sasquatch so he
// appears from behind them.
// Exports: createNearForest(assets) -> scene element

import { config } from '../config.js';

export function createNearForest(assets) {
  return {
    draw(ctx, time) {
      ctx.drawImage(assets.timeImage(config.files.nearForest, time), 0, 0);
    },
  };
}
