// farbird.js — a tiny distant bird crossing the sky (lives inside the sky
// group, so it passes behind the mountains). Clicking one counts as a bird
// (once per bird). Reward (bird_watcher): it turns gold too.
// Exports: createFarBird(assets) -> scene element with events.farbird and pointer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createCrossing, entryX } from './crossing.js';
import { createSparkles } from './sparkles.js';
import { randomBetween, randomDirection } from '../random.js';
import { isUnlocked, track } from '../achievements.js';
import { inRect } from '../geometry.js';

export function createFarBird(assets) {
  const opening = assets.manifest.window_opening;
  const sprite = createSprite(assets.animation('bird_far'));
  const shiny = createSprite(assets.animation('bird_far_shiny'));
  const sparkles = createSparkles(assets);
  const settings = config.farBird;
  let flights = [];   // { crossing, clicked }

  // Any option left out is picked at random. Returns false if the sky is full.
  function fly({ direction = randomDirection(), x, y, speedPxPerSec = settings.speedPxPerSec } = {}) {
    if (flights.length >= settings.maxAtOnce) return false;
    flights.push({
      crossing: createCrossing(sprite, {
        direction,
        x: x ?? entryX(direction, sprite, opening),
        y: y ?? Math.round(randomBetween(...settings.flightHeightPx)),
        speedPxPerSec,
        opening,
      }),
      clicked: false,
    });
    return true;
  }

  const flightAt = (x, y) => (inRect(x, y, opening)
    ? flights.find((f) => f.crossing.contains(x, y, config.achievements.clickPaddingPx)) : undefined);

  return {
    update(dtMs) {
      for (const flight of flights) flight.crossing.update(dtMs);
      flights = flights.filter((flight) => !flight.crossing.done());
      sparkles.update(dtMs);
    },
    draw(ctx, time) {
      const sheet = isUnlocked('bird_watcher') ? shiny : sprite;
      for (const flight of flights) flight.crossing.draw(ctx, time, sheet);
      sparkles.draw(ctx, time);
    },
    events: { farbird: fly },
    pointer: {
      contains: (x, y) => flightAt(x, y) !== undefined,
      setHovered() {},
      click(x, y) {
        const flight = flightAt(x, y);
        if (!flight || flight.clicked) return;
        flight.clicked = true;
        sparkles.spawn(x, y);
        track('birdClicks', 1);
      },
    },
  };
}
