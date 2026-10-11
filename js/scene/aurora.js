// aurora.js — northern lights over the night sky, under the stars (it is in
// the sky group, so clipped to the sky). Reward (around_the_clock): once
// earned, each night has config.achievements.auroraChancePerNight of showing
// them; they fade in, waver on a loop, and fade out when the night ends.
// Exports: createAurora(assets, { timeOfDay }) -> scene element with events.aurora
//   events.aurora() shows them tonight regardless of the roll (for testing).

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { isUnlocked } from '../achievements.js';

export function createAurora(assets, { timeOfDay }) {
  const animation = assets.animation('aurora');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const settings = config.achievements;
  let elapsedMs = 0;
  let wasEligible = false;
  let showingTonight = false;
  let opacity = 0;

  // Rolled once per night (or the moment it is earned during a night).
  function update(dtMs) {
    elapsedMs += dtMs;
    const eligible = timeOfDay.current() === 'night' && isUnlocked('around_the_clock');
    if (eligible && !wasEligible) showingTonight = Math.random() < settings.auroraChancePerNight;
    wasEligible = eligible;
    const target = eligible && showingTonight ? 1 : 0;
    const step = dtMs / settings.auroraFadeMs;
    opacity = target > opacity ? Math.min(target, opacity + step) : Math.max(target, opacity - step);
  }

  return {
    update,
    draw(ctx, time) {
      if (time !== 'night' || opacity <= 0) return;
      ctx.globalAlpha = opacity;
      sprite.draw(ctx, time, sprite.frameAt(elapsedMs), x, y);
    },
    events: {
      aurora() {
        if (!(timeOfDay.current() === 'night' && isUnlocked('around_the_clock'))) return false;
        showingTonight = true;
        wasEligible = true;   // this counts as tonight's roll, so it isn't rolled again
        return true;
      },
    },
  };
}
