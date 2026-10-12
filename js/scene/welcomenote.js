// welcomenote.js — the welcome note. On a visitor's first visit a sasquatch
// reaches in from outside the window and leaves a folded note on the sill
// (the `welcomeNote` event; main.js sends it a moment after the page opens).
// Hover the note for an outline; click it and it unfolds into the welcome
// note pop-up (js/note-popup.js). Closing that puts the note away for good.
// Two draw layers: `arm`, before the window frame so the frame hides where
// it reaches in from, and the element itself, a sill item after the frame.
// The saved progress keeps what happened (the `welcomeNote` stat: 1 left on
// the sill, 2 read), so a note left unread is still there next visit and a
// read one never comes back. While unread it is a sill item (js/sill.js):
// `rm note` / `touch note`.
// Exports: createWelcomeNote(assets, { progress, popup, timeOfDay })
//   -> scene element with arm and events.welcomeNote

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createOutline } from '../outline.js';
import { addSillItem, markOnSill, markOffSill } from '../sill.js';

const STAT = 'welcomeNote';
const LEFT = 1;   // left on the sill, unread
const READ = 2;

export function createWelcomeNote(assets, { progress, popup, timeOfDay }) {
  const arm = placedSprite(assets, 'note_deliver');
  const still = placedSprite(assets, 'note_sill');
  const unfolding = placedSprite(assets, 'note_open');
  const { release_frame: releaseFrame } = assets.animation('note_deliver').info;
  const outline = createOutline(assets.animation('note_sill'), config.hoverOutlineColour);
  const stage = () => progress.stats()[STAT] ?? 0;

  // away -> waiting -> delivering -> resting -> opening -> open -> away (read)
  let state = 'away';
  let elapsedMs = 0;
  let waitMs = 0;
  let hovered = false;

  function enter(next) {
    state = next;
    elapsedMs = 0;
    hovered = false;
  }

  function rest() {
    enter('resting');
    markOnSill('note');
  }
  if (stage() === LEFT) rest();   // left here on an earlier visit

  // The delivery, `afterSec` from now. Returns false if this visitor has
  // already had their note (or it is on its way).
  function deliver({ afterSec = 0 } = {}) {
    if (state !== 'away' || stage() !== 0) return false;
    enter('waiting');
    waitMs = afterSec * 1000;
    return true;
  }

  function close() {
    popup.hide();
    progress.setStat(STAT, READ);
    enter('away');
    markOffSill('note');
  }

  addSillItem('note', {
    available: () => stage() === LEFT,
    put: rest,
    take() {
      if (state === 'open') popup.hide();
      enter('away');
    },
    busy: () => ['delivering', 'opening'].includes(state),
  });

  const landed = () => state === 'delivering' && arm.frameAt(elapsedMs) >= releaseFrame;

  return {
    update(dtMs) {
      if (state === 'resting' && stage() !== LEFT) {   // `reset` forgets the note
        enter('away');
        markOffSill('note');
      }
      if (state === 'waiting') {
        waitMs -= dtMs;
        if (waitMs <= 0) enter('delivering');
        return;
      }
      if (state !== 'delivering' && state !== 'opening') return;
      elapsedMs += dtMs;
      if (state === 'delivering') {
        if (landed() && stage() === 0) {
          progress.setStat(STAT, LEFT);
          markOnSill('note');
        }
        if (elapsedMs >= arm.durationMs) enter('resting');
      } else if (elapsedMs >= unfolding.durationMs) {
        enter('open');
        popup.show(close, { night: timeOfDay.current() === 'night' });
      }
    },
    // The note on the sill: dropped there, resting, or unfolding. Hidden while open.
    draw(ctx, time) {
      if (state === 'resting') {
        if (hovered) ctx.drawImage(outline.image, still.left - 1, still.top - 1);
        still.draw(ctx, time, 0);
      } else if (landed()) {
        still.draw(ctx, time, 0);
      } else if (state === 'opening') {
        unfolding.draw(ctx, time, unfolding.frameAt(elapsedMs));
      }
    },
    // The arm, outside the window.
    arm: {
      draw(ctx, time) {
        if (state === 'delivering') arm.draw(ctx, time, arm.frameAt(elapsedMs));
      },
    },
    events: { welcomeNote: deliver },
    pointer: {
      contains: (x, y) => state === 'resting' && outline.covers(x - still.left, y - still.top),
      setHovered(on) { hovered = on; },
      click() { if (state === 'resting') enter('opening'); },
    },
  };
}

// A sprite at its manifest placement, with its top-left corner worked out.
function placedSprite(assets, name) {
  const animation = assets.animation(name);
  const sprite = createSprite(animation);
  const { x, y } = animation.info.placement;
  const [anchorX, anchorY] = animation.info.anchor;
  return {
    left: x - anchorX,
    top: y - anchorY,
    durationMs: sprite.durationMs,
    frameAt: (ms) => Math.min(sprite.frameAt(ms), animation.info.frames - 1),
    draw: (ctx, time, frame) => sprite.draw(ctx, time, frame, x, y),
  };
}
