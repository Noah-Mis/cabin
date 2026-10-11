// bird.js — a bird flapping across the view, left-to-right or right-to-left,
// bobbing gently as it goes, with a flutter of wings from the side it
// enters on. Clicking one counts it (once per bird).
// Reward (bird_watcher): golden birds that leave a trail of sparkles.
// Exports: createBird(assets) -> scene element with events.bird and pointer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createCrossing, entryX } from './crossing.js';
import { createSparkles } from './sparkles.js';
import { randomBetween, randomDirection } from '../random.js';
import { isUnlocked, track } from '../achievements.js';
import { inRect } from '../geometry.js';
import { play } from '../sound.js';

export function createBird(assets) {
  const opening = assets.manifest.window_opening;
  const sprite = createSprite(assets.animation('bird_flap'));
  const shiny = createSprite(assets.animation('bird_flap_shiny'));
  const sparkles = createSparkles(assets);
  const settings = config.bird;
  const rewards = config.achievements;
  let flights = [];   // { crossing, clicked, sinceSparkleMs }

  // Any option left out is picked at random. Returns false if the sky is full.
  function fly({ direction = randomDirection(), x, y } = {}) {
    if (flights.length >= settings.maxAtOnce) return false;
    const crossing = createCrossing(sprite, {
      direction,
      x: x ?? entryX(direction, sprite, opening),
      y: y ?? Math.round(randomBetween(...settings.flightHeightPx)),
      speedPxPerSec: settings.speedPxPerSec,
      bobAmplitudePx: settings.bobAmplitudePx,
      bobRadPerSec: settings.bobRadPerSec,
      opening,
    });
    flights.push({ crossing, clicked: false, sinceSparkleMs: 0 });
    play('bird', { pan: -direction * config.sound.sounds.bird.panPerSide });
    return true;
  }

  function dropTrail(flight, dtMs) {
    flight.sinceSparkleMs += dtMs;
    if (flight.sinceSparkleMs < rewards.birdSparkleEveryMs) return;
    flight.sinceSparkleMs = 0;
    const { x, y } = flight.crossing.position();
    sparkles.spawn(x - flight.crossing.direction * rewards.birdSparkleBehindPx, y);
  }

  const flightAt = (x, y) => (inRect(x, y, opening)
    ? flights.find((f) => f.crossing.contains(x, y, rewards.clickPaddingPx)) : undefined);

  return {
    update(dtMs) {
      const golden = isUnlocked('bird_watcher');
      for (const flight of flights) {
        flight.crossing.update(dtMs);
        if (golden) dropTrail(flight, dtMs);
      }
      flights = flights.filter((flight) => !flight.crossing.done());
      sparkles.update(dtMs);
    },
    draw(ctx, time) {
      sparkles.draw(ctx, time);   // behind the birds
      const sheet = isUnlocked('bird_watcher') ? shiny : sprite;
      for (const flight of flights) flight.crossing.draw(ctx, time, sheet);
    },
    events: { bird: fly },
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
