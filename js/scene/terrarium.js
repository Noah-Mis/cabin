// terrarium.js — the clay pot on its shelf on the left interior wall, and
// the field journal it opens (js/terrarium-journal.js). Hover the pot for an
// outline; click it to open the journal, click it (or anywhere outside the
// journal) again to close. The game itself is js/terrarium.js; this keeps it
// ticking every config.terrarium.tickSec while the page is open.
// The journal is a top-layer modal, so it is a separate element, `journal`,
// which layers.js puts above everything else (weather and sill items too).
// Keyboard: a visually hidden "Terrarium" button after the prompt, like the
// board's; while it has focus the pot shows its outline.
// What is growing shows in the pot: the species' codex portrait, behind the
// rim, revealed from the bottom up as it grows (a seed shows nothing, the
// flower only once it blooms); browned when withered, a little dry when
// wilting. Clicking the plant opens the journal too.
// Exports: createTerrariumPot(assets, { terrarium, journal }) -> scene element with pointer and journal
//   terrarium: from js/terrarium.js; journal: from js/terrarium-journal.js

import { config } from '../config.js';
import { createOutline } from '../outline.js';
import { inRect } from '../geometry.js';
import { speciesIndex } from '../terrarium-species.js';

const BLOOM_FROM = 0.85;                 // growth at which the plant is fully shown (in bloom)
const SPROUT_FROM = 0.15;                // before this it is a seed under the soil
const DRY = '#76603E';                   // the withered tile's stalk colour
const TINT = { dead: 0.8, wilting: 0.3 };

export function createTerrariumPot(assets, { terrarium, journal }) {
  const animation = assets.animation('terrarium_potshelf');
  const { x, y } = animation.info.placement;
  const outline = createOutline(animation, config.hoverOutlineColour);
  const codex = assets.animation('terrarium_codex');
  const plantAt = animation.info.plant;
  const size = codex.info.frame_w;
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

  // The first opaque row of each species' portrait: the plant's full height.
  const topRow = (() => {
    const c = document.createElement('canvas');
    c.width = c.height = size;
    const cx = c.getContext('2d', { willReadFrequently: true });
    return Array.from({ length: codex.info.frames }, (_, i) => {
      cx.clearRect(0, 0, size, size);
      cx.drawImage(codex.imageFor('day'), i * size, 0, size, size, 0, 0, size, size);
      const alpha = cx.getImageData(0, 0, size, size).data;
      for (let row = 0; row < size; row++) {
        for (let col = 0; col < size; col++) if (alpha[(row * size + col) * 4 + 3]) return row;
      }
      return size;
    });
  })();

  // How many rows of the portrait show, counting the ones behind the rim:
  // the plant's height above the rim, in proportion to its growth.
  function shownRows(pot) {
    if (pot.growth < SPROUT_FROM && !pot.dead) return 0;
    const above = size - plantAt.rim_rows - topRow[speciesIndex(pot.species)];
    return plantAt.rim_rows + Math.max(1, Math.round(above * Math.min(1, pot.growth / BLOOM_FROM)));
  }

  // The portrait for this species and time, browned if withered or wilting.
  const tinted = new Map();
  function portrait(pot, time) {
    const state = pot.dead ? 'dead' : pot.wilting ? 'wilting' : 'fine';
    const index = speciesIndex(pot.species);
    const key = `${time}|${index}|${state}`;
    if (!tinted.has(key)) {
      const c = document.createElement('canvas');
      c.width = c.height = size;
      const cx = c.getContext('2d');
      cx.drawImage(codex.imageFor(time), index * size, 0, size, size, 0, 0, size, size);
      if (state !== 'fine') {
        cx.globalCompositeOperation = 'source-atop';
        cx.globalAlpha = TINT[state];
        cx.fillStyle = DRY;
        cx.fillRect(0, 0, size, size);
      }
      tinted.set(key, c);
    }
    return tinted.get(key);
  }

  // The part of the portrait showing now, in canvas pixels (or null).
  function plantRect() {
    const pot = terrarium.get().pot;
    const rows = pot ? shownRows(pot) : 0;
    if (!rows) return null;
    return { x: x + plantAt.x, y: y + plantAt.y + size - rows, w: size, h: rows };
  }

  return {
    update(dtMs) {
      journal.update(dtMs);   // its tools' animations
      sinceTickMs += dtMs;
      if (sinceTickMs < config.terrarium.tickSec * 1000) return;
      sinceTickMs = 0;
      terrarium.tick();
    },
    draw(ctx, time) {
      if ((hovered || focused) && !journal.isOpen()) ctx.drawImage(outline.image, x - 1, y - 1);
      const shown = plantRect();
      if (shown) {   // behind the pot, so its base disappears into the rim
        const pot = terrarium.get().pot;
        ctx.drawImage(portrait(pot, time), 0, size - shown.h, size, shown.h, shown.x, shown.y, size, shown.h);
      }
      ctx.drawImage(animation.imageFor(time), x, y);
    },
    pointer: {
      contains(px, py) {
        const shown = plantRect();
        return outline.covers(px - x, py - y) || (!!shown && inRect(px, py, shown));
      },
      setHovered(on) { hovered = on; },
      click: toggle,
    },
    journal: {
      draw: journal.draw,
      pointer: journal.pointer,
    },
  };
}
