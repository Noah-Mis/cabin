// shootingstars.js — a streak falling across the night sky now and then (in
// the sky group, so clipped to the sky). Reward (night_owl): the scheduled
// `shootingstar` event only does anything once earned, and only at night.
// Each one plays once at a random spot in the region the JSON gives.
// Exports: createShootingStars(assets, { timeOfDay }) -> scene element with events.shootingstar

import { createSprite } from '../sprite.js';
import { randomBetween } from '../random.js';
import { isUnlocked } from '../achievements.js';

export function createShootingStars(assets, { timeOfDay }) {
  const animation = assets.animation('shooting_star');
  const sprite = createSprite(animation);
  const region = parseRegion(animation.info.placement.region);
  let stars = [];   // { x, y, elapsedMs }

  // Top-left (x, y) is random in the region if left out. Returns false when
  // it can't happen (not earned, or not night).
  function shoot({ x = Math.round(randomBetween(...region.x)), y = Math.round(randomBetween(...region.y)) } = {}) {
    if (!isUnlocked('night_owl') || timeOfDay.current() !== 'night') return false;
    stars.push({ x, y, elapsedMs: 0 });
    return true;
  }

  return {
    update(dtMs) {
      for (const star of stars) star.elapsedMs += dtMs;
      stars = stars.filter((star) => !sprite.isFinished(star.elapsedMs));
    },
    draw(ctx, time) {
      if (time !== 'night') return;
      for (const star of stars) sprite.draw(ctx, time, sprite.frameAt(star.elapsedMs), star.x, star.y);
    },
    events: { shootingstar: shoot },
  };
}

// The JSON describes the region in words, e.g. "night sky, x 60-240, y 26-50".
function parseRegion(text) {
  const range = (axis) => text.match(new RegExp(`${axis}\\s*(\\d+)\\s*-\\s*(\\d+)`)).slice(1).map(Number);
  return { x: range('x'), y: range('y') };
}
