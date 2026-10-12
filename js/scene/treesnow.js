// treesnow.js — snow settling on the pine forest while it snows: still
// overlays in stages, from a light dusting to a heavy blanket. One number,
// `amount` (0 to the number of stages), drives both layers: 0-1 fades the
// first stage in, then each whole step is one stage, the next cross-fading in
// over the one below. It climbs while it snows and falls back when it stops.
// Two draw layers, always at the same stage: `far` on the hill forest (right
// after the background) and the element itself on the front trees (right
// after the near forest).
// Exports: createTreeSnow(assets, { weather }) -> scene element with far and amount()

import { config } from '../config.js';

export function createTreeSnow(assets, { weather }) {
  const { info, imageFor } = assets.overlay('tree_snow');
  const { fadeSec, stageUpSec, stageDownSec } = config.treeSnow;
  let amount = 0;

  function draw(layer, ctx, time) {
    if (amount <= 0) return;
    const stage = Math.max(1, Math.floor(amount));
    ctx.globalAlpha = Math.min(1, amount);
    ctx.drawImage(imageFor(layer, time, stage), 0, 0);
    const next = amount - stage;   // how far the next stage has cross-faded in
    if (stage < info.stages && next > 0) {
      ctx.globalAlpha = next;
      ctx.drawImage(imageFor(layer, time, stage + 1), 0, 0);
    }
  }

  return {
    update(dtMs) {
      const snowing = weather.get() === 'snow';
      const perStageSec = amount < 1 || (!snowing && amount <= 1) ? fadeSec : snowing ? stageUpSec : stageDownSec;
      const step = dtMs / 1000 / perStageSec;
      amount = Math.max(0, Math.min(info.stages, amount + (snowing ? step : -step)));
      // Steps of 1/30 add up to 0.9999…, not 1: snap onto a whole stage when that close.
      if (Math.abs(amount - Math.round(amount)) < 1e-9) amount = Math.round(amount);
    },
    draw: (ctx, time) => draw('near', ctx, time),
    far: { draw: (ctx, time) => draw('far', ctx, time) },
    amount: () => amount,
  };
}
