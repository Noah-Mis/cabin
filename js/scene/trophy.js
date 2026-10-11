// trophy.js — a gold trophy at the left of the sill, catching the light now
// and then. Reward (woodsman); not drawn until earned. A sill item, so it is
// drawn after the window frame.
// Exports: createTrophy(assets) -> scene element

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createSparkles } from './sparkles.js';
import { randomBetween } from '../random.js';
import { isUnlocked } from '../achievements.js';

export function createTrophy(assets) {
  const animation = assets.animation('trophy');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const [anchorX, anchorY] = animation.info.anchor;
  const sparkles = createSparkles(assets);
  const nextSparkleMs = () => randomBetween(...config.achievements.trophySparkleEverySec) * 1000;
  let untilSparkleMs = nextSparkleMs();

  // A random spot on the trophy itself, in scene pixels.
  function spotOnTrophy() {
    return [
      Math.round(x - anchorX + randomBetween(0, sprite.width)),
      Math.round(y - anchorY + randomBetween(0, sprite.height / 2)),   // the cup, not the base
    ];
  }

  return {
    update(dtMs) {
      sparkles.update(dtMs);
      if (!isUnlocked('woodsman')) return;
      untilSparkleMs -= dtMs;
      if (untilSparkleMs > 0) return;
      untilSparkleMs = nextSparkleMs();
      sparkles.spawn(...spotOnTrophy());
    },
    draw(ctx, time) {
      if (!isUnlocked('woodsman')) return;
      sprite.draw(ctx, time, 0, x, y);
      sparkles.draw(ctx, time);
    },
  };
}
