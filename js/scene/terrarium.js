// terrarium.js — the clay pot on its shelf on the left interior wall, and
// the field journal it opens (js/terrarium-journal.js). Hover the pot for an
// outline; click it to open the journal, click it (or anywhere outside the
// journal) again to close. The game itself is js/terrarium.js; this keeps it
// ticking every config.terrarium.tickSec while the page is open.
// The journal is a top-layer modal, so it is a separate element, `journal`,
// which layers.js puts above everything else (weather and sill items too).
// Keyboard: a visually hidden "Terrarium" button after the prompt, like the
// board's; while it has focus the pot shows its outline.
// Exports: createTerrariumPot(assets, { terrarium, journal }) -> scene element with pointer and journal
//   terrarium: from js/terrarium.js; journal: from js/terrarium-journal.js

import { config } from '../config.js';
import { createOutline } from '../outline.js';

export function createTerrariumPot(assets, { terrarium, journal }) {
  const animation = assets.animation('terrarium_potshelf');
  const { x, y } = animation.info.placement;
  const outline = createOutline(animation, config.hoverOutlineColour);
  let hovered = false;
  let focused = false;
  let sinceTickMs = 0;

  function toggle() {
    if (journal.isOpen()) journal.close();
    else journal.open();
  }

  const focusTarget = document.createElement('button');
  focusTarget.type = 'button';
  focusTarget.className = 'scene-hotspot';
  focusTarget.textContent = config.terrarium.words.label;
  focusTarget.dataset.keepFocus = '';
  focusTarget.addEventListener('focus', () => { focused = true; });
  focusTarget.addEventListener('blur', () => { focused = false; });
  focusTarget.addEventListener('click', toggle);
  document.body.append(focusTarget);

  return {
    update(dtMs) {
      sinceTickMs += dtMs;
      if (sinceTickMs < config.terrarium.tickSec * 1000) return;
      sinceTickMs = 0;
      terrarium.tick();
    },
    draw(ctx, time) {
      if ((hovered || focused) && !journal.isOpen()) ctx.drawImage(outline.image, x - 1, y - 1);
      ctx.drawImage(animation.imageFor(time), x, y);
    },
    pointer: {
      contains: (px, py) => outline.covers(px - x, py - y),
      setHovered(on) { hovered = on; },
      click: toggle,
    },
    journal: {
      draw: journal.draw,
      pointer: journal.pointer,
    },
  };
}
