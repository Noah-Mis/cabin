// stars.js — twinkling stars. The sheet only exists for night, so on other
// times of day there is simply nothing to draw. At night the stars listed in
// achievements.json can be clicked; each counts once per night and sparkles.
// Reward (stargazer): the sasquatch constellation in the night sky.
// Lives in the sky group, so all of this is clipped to the sky.
// Exports: createStars(assets, { timeOfDay }) -> scene element with pointer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createSparkles } from './sparkles.js';
import { isUnlocked, track } from '../achievements.js';
import { withinRadius } from '../geometry.js';

export function createStars(assets, { timeOfDay }) {
  const animation = assets.animation('stars');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const targets = assets.packManifest(config.achievements.artDir).star_click_targets;
  const constellationAnimation = assets.animation('constellation_sasquatch');
  const constellation = createSprite(constellationAnimation);
  const sparkles = createSparkles(assets);
  let elapsedMs = 0;
  let clickedTonight = new Set();   // indexes into targets
  let wasNight = false;

  const isNight = () => timeOfDay.current() === 'night';
  // The nearest star within reach: some stars are closer together than the
  // click radius, and a click belongs to the one it is nearest.
  function starAt(px, py) {
    if (!isNight()) return -1;
    let best = -1;
    let bestDistance = Infinity;
    targets.forEach(([sx, sy], index) => {
      const distance = (px - sx) ** 2 + (py - sy) ** 2;
      if (distance < bestDistance && withinRadius(px, py, sx, sy, config.achievements.starClickRadiusPx)) {
        best = index;
        bestDistance = distance;
      }
    });
    return best;
  }

  return {
    update(dtMs) {
      elapsedMs += dtMs;
      sparkles.update(dtMs);
      if (isNight() && !wasNight) clickedTonight = new Set();   // a new night
      wasNight = isNight();
    },
    draw(ctx, time) {
      sprite.draw(ctx, time, sprite.frameAt(elapsedMs), x, y);
      if (time === 'night' && isUnlocked('stargazer')) {
        const { x: cx, y: cy } = constellationAnimation.info.placement;
        constellation.draw(ctx, time, 0, cx, cy);
      }
      if (time === 'night') sparkles.draw(ctx, time);
    },
    pointer: {
      contains: (px, py) => starAt(px, py) >= 0,
      setHovered() {},
      click(px, py) {
        const index = starAt(px, py);
        if (index < 0 || clickedTonight.has(index)) return;
        clickedTonight.add(index);
        sparkles.spawn(...targets[index]);
        track('starClicks', 1);
      },
    },
  };
}
