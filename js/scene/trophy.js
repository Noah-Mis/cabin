// trophy.js — a gold trophy at the left of the sill, catching the light now
// and then. Reward (woodsman); not drawn until earned. A sill item, so it is
// drawn after the window frame, and in js/sill.js: it arrives when earned,
// goes on `reset`, and `rm trophy` / `touch trophy` put it away and back.
// Exports: createTrophy(assets) -> scene element

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createSparkles } from './sparkles.js';
import { randomBetween } from '../random.js';
import { isUnlocked } from '../achievements.js';
import { addSillItem, isOnSill, markOnSill, markOffSill } from '../sill.js';

export function createTrophy(assets) {
  const animation = assets.animation('trophy');
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const [anchorX, anchorY] = animation.info.anchor;
  const sparkles = createSparkles(assets);
  const nextSparkleMs = () => randomBetween(...config.achievements.trophySparkleEverySec) * 1000;
  let untilSparkleMs = nextSparkleMs();
  let earned = false;

  function followReward() {
    if (isUnlocked('woodsman') === earned) return;
    earned = !earned;
    if (earned) markOnSill('trophy');
    else markOffSill('trophy');
  }

  addSillItem('trophy', {
    available: () => isUnlocked('woodsman'),
    put: () => markOnSill('trophy'),
    take() {},
    busy: () => false,
    follow: followReward,
  });

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
      if (!isOnSill('trophy')) return;
      untilSparkleMs -= dtMs;
      if (untilSparkleMs > 0) return;
      untilSparkleMs = nextSparkleMs();
      sparkles.spawn(...spotOnTrophy());
    },
    draw(ctx, time) {
      if (!isOnSill('trophy')) return;
      sprite.draw(ctx, time, 0, x, y);
      sparkles.draw(ctx, time);
    },
  };
}
