// board.js — the achievement board hanging on the window's right-hand log:
// a gold pin in its hole for each of the first twelve achievements once
// earned, and a gold star at the top for the last. Each new pin appears with
// a sparkle. Hover it for an outline; click it to open the board pop-up
// (js/board-popup.js). Every position is in anim/board/board_layout.json.
// Hung on the cabin, so it is drawn after the window frame.
// Keyboard: a visually hidden "Achievements" button sits right after the
// prompt, so Tab from the terminal reaches it; while it has focus the board
// shows its hover outline, and Enter or Space opens the pop-up.
// Exports: loadBoardArt() -> Promise<{ layout, images }>
//          createBoard(assets, { layout, images, popup }) -> scene element with pointer
//   images: { board: imageFor(time), pin, star }

import { config } from '../config.js';
import { loadJson, loadImage, pickFilesByTime } from '../assets.js';
import { createOutline } from '../outline.js';
import { createSparkles } from './sparkles.js';
import { inRect } from '../geometry.js';
import { isUnlocked, listAchievements } from '../achievements.js';

// The layout file and the board's own art (plain by day, _night at night).
export async function loadBoardArt() {
  const dir = config.board.artDir;
  const layout = await loadJson(config.board.layoutFile);
  const { board } = layout;
  const byTime = pickFilesByTime(board.files, config.times);
  const boardFiles = [...new Set(Object.values(byTime))];
  const [pin, star, ...boards] = await Promise.all(
    [board.pin.file, board.star.file, ...boardFiles].map((file) => loadImage(dir + file)),
  );
  const boardImages = Object.fromEntries(boardFiles.map((file, i) => [file, boards[i]]));
  return { layout, images: { board: (time) => boardImages[byTime[time]], pin, star } };
}

export function createBoard(assets, { layout, images, popup }) {
  const { board } = layout;
  const box = { x: board.canvas_x, y: board.canvas_y, w: board.w, h: board.h };
  const outline = createOutline(
    { info: { frame_w: board.w, frame_h: board.h, frames: 1 }, imageFor: images.board },
    config.hoverOutlineColour,
  );
  const sparkles = createSparkles(assets);
  let hovered = false;
  let focused = false;

  // Which mark each achievement gets: the star for the one the layout names,
  // pins in order for the rest. [{ id, image, x, y }] in canvas pixels.
  const marks = (() => {
    const ids = listAchievements().map((entry) => entry.definition.id);
    const pins = ids.filter((id) => id !== board.star.for);
    return [
      ...pins.slice(0, board.pin.positions.length).map((id, i) => mark(id, images.pin, board.pin.positions[i])),
      mark(board.star.for, images.star, board.star.position),
    ];
  })();
  function mark(id, image, [x, y]) {
    return { id, image, x: box.x + x, y: box.y + y };
  }

  let shown = new Set(marks.filter((m) => isUnlocked(m.id)).map((m) => m.id));

  function open() {
    if (!popup.isShown()) popup.show(() => popup.hide());
  }

  const focusTarget = document.createElement('button');
  focusTarget.type = 'button';
  focusTarget.className = 'scene-hotspot';
  focusTarget.textContent = config.board.words.label;
  focusTarget.dataset.keepFocus = '';   // Enter and Space reach it; the terminal does not take focus back
  focusTarget.addEventListener('focus', () => { focused = true; });
  focusTarget.addEventListener('blur', () => { focused = false; });
  focusTarget.addEventListener('click', open);
  document.body.append(focusTarget);   // after the prompt: one Tab from the terminal reaches it

  return {
    update(dtMs) {
      // New pins sparkle once; a reset empties the board, all without a reload.
      const now = new Set(marks.filter((m) => isUnlocked(m.id)).map((m) => m.id));
      for (const m of marks) {
        if (now.has(m.id) && !shown.has(m.id)) {
          sparkles.spawn(m.x + Math.floor(m.image.width / 2), m.y + Math.floor(m.image.height / 2));
        }
      }
      shown = now;
      sparkles.update(dtMs);
    },
    draw(ctx, time) {
      if (hovered || focused) ctx.drawImage(outline.image, box.x - 1, box.y - 1);
      ctx.drawImage(images.board(time), box.x, box.y);
      for (const m of marks) if (isUnlocked(m.id)) ctx.drawImage(m.image, m.x, m.y);
      sparkles.draw(ctx, time);
    },
    pointer: {
      contains: (x, y) => inRect(x, y, box),
      setHovered(on) { hovered = on; },
      click: open,
    },
  };
}
