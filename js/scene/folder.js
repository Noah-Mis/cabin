// folder.js — my folder (résumé, about me, ...). The `whoami` command slides
// it onto the sill, where it stays. Hover it for an outline; click to open
// it, and click the open folder to close it again. What shows up once it is
// open lives in js/folder-contents.js.
// Reward (case_closed): the gold-seal folder everywhere: sliding onto the
// sill, at rest, opening, and closing (its own closing sheet; the plain folder plays its opening
// backwards).
// Exports: createFolder(assets) -> scene element with events.folder and pointer

import { config } from '../config.js';
import { createSprite } from '../sprite.js';
import { createOutline } from '../outline.js';
import { folderContents } from '../folder-contents.js';
import { isUnlocked } from '../achievements.js';

export function createFolder(assets) {
  const opened = placedSprite(assets, 'folder_opened');   // both folders open to the same page
  const sheets = {
    plain: {
      placing: placedSprite(assets, 'folder_place'),
      closed: placedSprite(assets, 'folder'),
      opening: placedSprite(assets, 'folder_open'),
      closing: { ...placedSprite(assets, 'folder_open'), backwards: true },
    },
    reviewed: {
      placing: placedSprite(assets, 'folder_reviewed_place'),
      closed: placedSprite(assets, 'folder_reviewed'),
      opening: placedSprite(assets, 'folder_reviewed_open'),
      closing: placedSprite(assets, 'folder_reviewed_close'),
    },
  };
  // The gold-seal folder has the same shape, so one closed outline serves both.
  const outlines = {
    closed: createOutline(assets.animation('folder'), config.hoverOutlineColour),
    open: createOutline(assets.animation('folder_opened'), config.hoverOutlineColour),
  };
  const current = () => sheets[isUnlocked('case_closed') ? 'reviewed' : 'plain'];

  // away -> placing -> closed <-> opening -> open -> closing -> closed
  let state = 'away';
  let elapsedMs = 0;
  let hovered = false;

  function enter(next) {
    state = next;
    elapsedMs = 0;
  }

  // Returns false if the folder is already out.
  function takeOut() {
    if (state !== 'away') return false;
    enter('placing');
    return true;
  }

  function close() {
    if (state !== 'open') return;
    enter('closing');
    folderContents.close();
  }

  // The still sprite (and its outline) for states the visitor can click.
  const resting = () => ({ closed: [current().closed, outlines.closed], open: [opened, outlines.open] })[state] ?? null;

  // What plays in each moving state, and where it leads.
  const playing = () => ({
    placing: [current().placing, 'closed'],
    opening: [current().opening, 'open'],
    closing: [current().closing, 'closed'],
  })[state];

  return {
    update(dtMs) {
      const now = playing();
      if (!now) return;
      elapsedMs += dtMs;
      const [sprite, next] = now;
      if (elapsedMs < sprite.durationMs) return;
      enter(next);
      if (next === 'open') folderContents.open({ close });
    },
    draw(ctx, time) {
      if (state === 'away') return;
      const still = resting();
      if (still) {
        const [sprite, outline] = still;
        if (hovered) ctx.drawImage(outline.image, sprite.left - 1, sprite.top - 1);
        sprite.draw(ctx, time, 0);
        return;
      }
      const [sprite] = playing();
      const frame = sprite.frameAt(elapsedMs);
      sprite.draw(ctx, time, sprite.backwards ? sprite.frames - 1 - frame : frame);
    },
    events: { folder: takeOut },
    pointer: {
      contains(x, y) {
        const still = resting();
        return still !== null && still[1].covers(x - still[0].left, y - still[0].top);
      },
      setHovered(on) { hovered = on; },
      click() {
        if (state === 'closed') enter('opening');
        else if (state === 'open') close();
      },
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
    frames: animation.info.frames,
    durationMs: sprite.durationMs,
    frameAt: (ms) => Math.min(sprite.frameAt(ms), animation.info.frames - 1),
    draw: (ctx, time, frame) => sprite.draw(ctx, time, frame, x, y),
  };
}
