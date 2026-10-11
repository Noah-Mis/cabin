// rainbow.js — a translucent arc over the falls after rain. Belongs with the
// weather: it watches the weather module, and when rain stops it fades in,
// stays for config.achievements.rainbowShowSec, and fades out. Drawn after
// the waterfall and before the near forest. Reward (storm_chaser).
// Exports: createRainbow(assets, { weather }) -> scene element with events.rainbow
//   events.rainbow() shows it now, as if rain had just stopped (for testing).

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { isUnlocked } from '../achievements.js';

export function createRainbow(assets, { weather }) {
  const animation = assets.animation('rainbow');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const settings = config.achievements;
  let previousWeather = weather.get();
  let shownMs = Infinity;   // time since it appeared; Infinity = not showing

  function appear() {
    if (!isUnlocked('storm_chaser')) return false;
    shownMs = 0;
    return true;
  }

  // Fades in, holds, fades out, all measured from when it appeared.
  function opacity() {
    const holdEnd = settings.rainbowFadeMs + settings.rainbowShowSec * 1000;
    if (shownMs < settings.rainbowFadeMs) return shownMs / settings.rainbowFadeMs;
    if (shownMs < holdEnd) return 1;
    return Math.max(0, 1 - (shownMs - holdEnd) / settings.rainbowFadeMs);
  }

  return {
    update(dtMs) {
      const now = weather.get();
      if (previousWeather === 'rain' && now !== 'rain') appear();
      previousWeather = now;
      shownMs += dtMs;
    },
    draw(ctx, time) {
      const alpha = opacity();
      if (alpha <= 0) return;
      ctx.globalAlpha = alpha;
      sprite.draw(ctx, time, 0, x, y);
    },
    events: { rainbow: appear },
  };
}
