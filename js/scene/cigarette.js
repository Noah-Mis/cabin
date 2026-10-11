// cigarette.js — an easter egg. The hidden `cig` command slides a pack of
// cigarettes onto the sill, where it stays. Hovering the pack outlines it;
// clicking it takes a cigarette out and smokes it, drawn over everything.
// What plays comes from the smoke manifest's sequences: "get_cigarette"
// (pack_place, then cig_pick) followed by "smoke". Smoking one to the end is
// tracked. Reward (smoke_break): an ashtray on the sill.
// Exports: createCigarette(assets) -> scene element with events.cig and pointer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createSequence } from '../sequence.js';
import { createOutline } from '../outline.js';
import { isUnlocked, track } from '../achievements.js';

const PLACE_STEP = 'pack_place';   // the get_cigarette step that puts the pack down

export function createCigarette(assets) {
  const packAnimation = assets.animation('cig_pack');
  const pack = createSprite(packAnimation);
  const { x: packX, y: packY } = packAnimation.info.placement;
  const packLeft = packX - packAnimation.info.anchor[0];
  const packTop = packY - packAnimation.info.anchor[1];
  const outline = createOutline(packAnimation, config.hoverOutlineColour);
  const { get_cigarette: getCigarette, smoke } = assets.sequences;
  const ashtrayAnimation = assets.animation('ashtray');
  const ashtray = createSprite(ashtrayAnimation);

  let packOnSill = false;
  let hovered = false;
  let run = null;   // { kind: 'place' | 'smoke', sequence, elapsedMs } while playing

  function play(kind, steps) {
    run = { kind, sequence: createSequence(assets, steps), elapsedMs: 0 };
  }

  // Returns false if the pack is already out (or on its way).
  function placePack() {
    if (packOnSill || run) return false;
    play('place', getCigarette.steps.filter((step) => step.play === PLACE_STEP));
    return true;
  }

  function smokeOne() {
    play('smoke', [...getCigarette.steps.filter((step) => step.play !== PLACE_STEP), ...smoke.steps]);
  }

  const clickable = () => packOnSill && !run;

  return {
    update(dtMs) {
      if (!run) return;
      run.elapsedMs += dtMs;
      if (run.elapsedMs < run.sequence.durationMs) return;
      if (run.kind === 'place') packOnSill = true;
      if (run.kind === 'smoke') track('smokesFinished', 1);
      run = null;
    },
    draw(ctx, time) {
      if (packOnSill) {
        if (hovered && clickable()) ctx.drawImage(outline.image, packLeft - 1, packTop - 1);
        pack.draw(ctx, time, 0, packX, packY);
      }
      if (isUnlocked('smoke_break')) {
        const { x, y } = ashtrayAnimation.info.placement;
        ashtray.draw(ctx, time, 0, x, y);
      }
      run?.sequence.draw(ctx, time, run.elapsedMs);
    },
    events: { cig: placePack },
    pointer: {
      contains: (x, y) => clickable() && outline.covers(x - packLeft, y - packTop),
      setHovered(on) { hovered = on; },
      click() { if (clickable()) smokeOne(); },
    },
  };
}
