// mug.js — the coffee cup on the sill with its steam, always running.
// Indoors, so it has one version plus a darker one for night. Hovering it
// outlines the cup; clicking it takes a sip: the cup lifts toward the
// viewer, tips, and returns, while the cup on the sill (and its steam) is
// hidden. The sip is drawn above everything else, so it is a separate
// element, `overlay`, which layers.js puts at the very top.
// Reward (caffeinated): the enamel camp mug, with its own sip.
// A sill item (js/sill.js): there from the start; `rm mug` / `touch mug`.
// Exports: createMug(assets) -> scene element with pointer and overlay

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createOutline } from '../outline.js';
import { isUnlocked, track } from '../achievements.js';
import { addSillItem, isOnSill, markOnSill } from '../sill.js';

export function createMug(assets) {
  const animation = assets.animation('mug');
  const cups = { plain: createSprite(animation), camp: createSprite(assets.animation('mug_camp')) };
  const sips = { plain: placed(assets, 'mug_sip'), camp: placed(assets, 'mug_camp_sip') };
  // The two cups share a shape; outline the part of it that never moves.
  const outline = createOutline(animation, config.hoverOutlineColour, { steadyOnly: true });
  const { x, y } = animation.info.placement;
  const left = x - animation.info.anchor[0];
  const top = y - animation.info.anchor[1];
  let elapsedMs = 0;
  let hovered = false;
  let sip = null;   // { sprite, elapsedMs } while the visitor drinks

  const kind = () => (isUnlocked('caffeinated') ? 'camp' : 'plain');
  const isOn = (px, py) => isOnSill('mug') && !sip && outline.covers(px - left, py - top);

  addSillItem('mug', {
    available: () => true,
    put: () => markOnSill('mug'),
    take: () => { hovered = false; },
    busy: () => sip !== null,
  }, ['cup', 'coffee']);
  markOnSill('mug');

  return {
    update(dtMs) {
      elapsedMs += dtMs;
      if (!sip) return;
      sip.elapsedMs += dtMs;
      if (sip.elapsedMs >= sip.sprite.durationMs) sip = null;
    },
    draw(ctx, time) {
      if (sip || !isOnSill('mug')) return;   // in the visitor's hand, or put away
      if (hovered) ctx.drawImage(outline.image, left - 1, top - 1);
      const cup = cups[kind()];
      cup.draw(ctx, time, cup.frameAt(elapsedMs), x, y);
    },
    pointer: {
      contains: isOn,
      setHovered(on) { hovered = on; },
      click(px, py) {
        if (!isOn(px, py)) return;
        sip = { sprite: sips[kind()], elapsedMs: 0 };
        hovered = false;
        track('mugClicks', 1);
      },
    },
    overlay: {
      draw(ctx, time) {
        if (sip) sip.sprite.draw(ctx, time, Math.max(0, sip.sprite.frameAt(sip.elapsedMs)));
      },
    },
  };
}

// A sheet at its manifest placement (these are placed by their top-left).
function placed(assets, name) {
  const animation = assets.animation(name);
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  return {
    durationMs: sprite.durationMs,
    frameAt: sprite.frameAt,
    draw: (ctx, time, frame) => sprite.draw(ctx, time, frame, x, y),
  };
}
