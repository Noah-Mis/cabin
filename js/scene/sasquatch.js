// sasquatch.js — he rises from a gap between two front treetops, looks
// around, and sinks back. Drawn before the near forest, which hides his body.
// Only one peek at a time, and only at the spots listed in the manifest.
// Clicking him while he shows counts once per appearance.
// Rewards: first_sighting — he waves (sasquatch_wave);
//          cryptid_hunter — sometimes it is the yeti (yeti_peek / yeti_wave).
// Exports: createSasquatch(assets) -> scene element with events.sasquatch and pointer

import { config } from '../config.js';
import { createSprite, drawnBoxes } from '../sprite.js';
import { randomItem } from '../random.js';
import { isUnlocked, track } from '../achievements.js';
import { inRect } from '../geometry.js';

export function createSasquatch(assets) {
  const spots = assets.animation('sasquatch_peek').info.placement.spots;
  const sheets = {};
  for (const name of ['sasquatch_peek', 'sasquatch_wave', 'yeti_peek', 'yeti_wave']) {
    const animation = assets.animation(name);
    sheets[name] = { sprite: createSprite(animation), boxes: drawnBoxes(animation), anchor: animation.info.anchor };
  }
  let peek = null;   // { spot, sheet, elapsedMs, clicked } while he is out

  // Which sheet this appearance uses, decided when he comes out. `creature`
  // ('sasquatch' or 'yeti') skips the roll, for testing.
  function chooseSheet(creature) {
    const rolled = isUnlocked('cryptid_hunter') && Math.random() < config.achievements.yetiChance ? 'yeti' : 'sasquatch';
    const who = creature ?? rolled;
    return sheets[`${who}_${isUnlocked('first_sighting') ? 'wave' : 'peek'}`];
  }

  // spotIndex picks a manifest spot; random if left out. Returns false if he
  // is already peeking.
  function peekOut({ spotIndex, creature } = {}) {
    if (peek) return false;
    const spot = spotIndex === undefined ? randomItem(spots) : spots[spotIndex];
    peek = { spot, sheet: chooseSheet(creature), elapsedMs: 0, clicked: false };
    return true;
  }

  // The drawn part of the current frame, padded, in scene pixels.
  function hitBox() {
    if (!peek) return null;
    const { sprite, boxes, anchor } = peek.sheet;
    const box = boxes[sprite.frameAt(peek.elapsedMs)];
    if (!box) return null;
    const pad = config.achievements.clickPaddingPx;
    return { x: peek.spot.x - anchor[0] + box.x - pad, y: peek.spot.y - anchor[1] + box.y - pad,
      w: box.w + 2 * pad, h: box.h + 2 * pad };
  }

  const isOn = (x, y) => { const box = hitBox(); return box !== null && inRect(x, y, box); };

  return {
    update(dtMs) {
      if (!peek) return;
      peek.elapsedMs += dtMs;
      if (peek.sheet.sprite.isFinished(peek.elapsedMs)) peek = null;
    },
    draw(ctx, time) {
      if (!peek) return;
      const { sprite } = peek.sheet;
      sprite.draw(ctx, time, sprite.frameAt(peek.elapsedMs), peek.spot.x, peek.spot.y);
    },
    events: { sasquatch: peekOut },
    pointer: {
      contains: isOn,
      setHovered() {},
      click(x, y) {
        if (!isOn(x, y) || peek.clicked) return;
        peek.clicked = true;
        track('sasquatchClicks', 1);
      },
    },
  };
}
