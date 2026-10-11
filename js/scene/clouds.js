// clouds.js — the four cloud shapes drifting slowly to the right. When one
// leaves the window opening it re-enters from the left edge.
// Exports: createClouds(assets) -> scene element

import { config } from '../config.js';
import { createSprite } from '../sprite.js';

export function createClouds(assets) {
  const opening = assets.manifest.window_opening;
  const clouds = config.clouds.map((cloud) => ({
    ...cloud,
    sprite: createSprite(assets.animation(cloud.sprite)),
  }));
  let elapsedMs = 0;

  // Wrap x into the span from "just hidden on the left" to the opening's right edge.
  function wrappedX(cloud) {
    const travelled = Math.floor(cloud.speedPxPerSec * elapsedMs / 1000);
    const left = opening.x - cloud.sprite.width;
    const span = opening.w + cloud.sprite.width;
    const offset = (cloud.x + travelled - left) % span;
    return left + (offset < 0 ? offset + span : offset);
  }

  return {
    update(dtMs) { elapsedMs += dtMs; },
    draw(ctx, time) {
      for (const cloud of clouds) cloud.sprite.draw(ctx, time, 0, wrappedX(cloud), cloud.y);
    },
  };
}
