// deer.js — a deer comes down to the water: it walks in, grazes, then walks
// on or back the way it came. Drawn before the near forest, like the
// sasquatch, so the trees overlap it. The trees never hide it completely, so
// it fades in and out at the ends of its walk. Reward (cabin_fever): the
// scheduled `deer` event only does anything once earned.
// Exports: createDeer(assets) -> scene element with events.deer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { isUnlocked } from '../achievements.js';

export function createDeer(assets) {
  const walkAnimation = assets.animation('deer_walk');
  const walk = createSprite(walkAnimation);
  const grazeAnimation = assets.animation('deer_graze');
  const graze = createSprite(grazeAnimation);
  const settings = config.achievements.deer;
  // The JSON gives the walk in words: "feet on y=123, enters from x 128 and stops near x 148".
  const path = walkAnimation.info.placement.path;
  const startX = Number(path.match(/from x (\d+)/)[1]);
  const { x: grazeX, y: groundY } = grazeAnimation.info.placement;
  const walkMs = (Math.abs(grazeX - startX) / settings.walkSpeedPxPerSec) * 1000;
  let visit = null;   // { phase: 'in' | 'graze' | 'out', elapsedMs, outDirection }

  // outDirection: +1 walks on, -1 goes back the way it came; random if left out.
  function arrive({ outDirection = Math.random() < 0.5 ? 1 : -1 } = {}) {
    if (!isUnlocked('cabin_fever') || visit) return false;
    visit = { phase: 'in', elapsedMs: 0, outDirection };
    return true;
  }

  // Where it is and which way it faces, for the current phase.
  function pose() {
    const step = Math.floor(settings.walkSpeedPxPerSec * visit.elapsedMs / 1000);
    const inDirection = Math.sign(grazeX - startX);
    if (visit.phase === 'in') return { x: startX + inDirection * step, direction: inDirection };
    if (visit.phase === 'graze') return { x: grazeX, direction: inDirection };
    return { x: grazeX + visit.outDirection * step, direction: visit.outDirection };
  }

  function opacity() {
    if (settings.fadeMs <= 0 || visit.phase === 'graze') return 1;
    const fromEdge = visit.phase === 'in' ? visit.elapsedMs : walkMs - visit.elapsedMs;
    return Math.max(0, Math.min(1, fromEdge / settings.fadeMs));
  }

  return {
    update(dtMs) {
      if (!visit) return;
      visit.elapsedMs += dtMs;
      const phaseMs = visit.phase === 'graze' ? graze.durationMs : walkMs;
      if (visit.elapsedMs < phaseMs) return;
      if (visit.phase === 'out') { visit = null; return; }
      visit.phase = visit.phase === 'in' ? 'graze' : 'out';
      visit.elapsedMs = 0;
    },
    draw(ctx, time) {
      if (!visit) return;
      const { x, direction } = pose();
      const sprite = visit.phase === 'graze' ? graze : walk;
      ctx.globalAlpha = opacity();
      sprite.draw(ctx, time, Math.max(0, sprite.frameAt(visit.elapsedMs)), x, groundY, direction < 0);
    },
    events: { deer: arrive },
  };
}
