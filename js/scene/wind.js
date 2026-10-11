// wind.js — a gust (with a little curl) or a plain streak sweeping right.
// Both play once and slide while they play, with the sound of a gust.
// Exports: createWind(assets) -> scene element with events.wind

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createCrossing } from './crossing.js';
import { randomBetween, randomItem } from '../random.js';
import { play } from '../sound.js';

export function createWind(assets) {
  const opening = assets.manifest.window_opening;
  const sprites = {
    gust: createSprite(assets.animation('wind_gust')),
    streak: createSprite(assets.animation('wind_streak')),
  };
  const settings = config.wind;
  let gusts = [];

  // kind: 'gust' or 'streak'. Anything left out is picked at random so the
  // whole sweep stays inside the opening. Returns false if it is too windy.
  function blow({ kind = randomItem(Object.keys(sprites)), x, y, speedPxPerSec = settings.speedPxPerSec } = {}) {
    if (gusts.length >= settings.maxAtOnce) return false;
    const sprite = sprites[kind];
    gusts.push(createCrossing(sprite, {
      direction: 1,
      x: x ?? Math.round(randomBetween(opening.x, opening.x + opening.w - 2 * sprite.width)),
      y: y ?? Math.round(randomBetween(...settings.heightPx)),
      speedPxPerSec,
      opening,
    }));
    const sweep = config.sound.sounds.wind.sweepPan;
    play('wind', { pan: -sweep, panTo: sweep });
    return true;
  }

  return {
    update(dtMs) {
      for (const gust of gusts) gust.update(dtMs);
      gusts = gusts.filter((gust) => !gust.done());
    },
    draw(ctx, time) {
      for (const gust of gusts) gust.draw(ctx, time);
    },
    events: { wind: blow },
  };
}
