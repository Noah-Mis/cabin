// board-popup.js — the pop-up that opens from the achievement board: every
// achievement in a slot (its badge, or the locked one), a gold frame on the
// selected slot, a note describing it, and a progress bar. Art is drawn at
// the canvas's pixel scale; every word is real text over the art's blank
// regions. Positions, sizes and colours come from the board layout file.
// The backdrop, scaling, plain fallback and closing are js/popup-frame.js.
// Exports: createBoardPopup(canvas, { bottomInset, layout, badges })
//            -> { show(onRequestClose), hide(), refresh(selectId), isShown() }
//   badges: the "badges" entry of achievements.json (sheet file and frame size).
//   refresh(selectId) redraws from the current progress (after an unlock or
//   a reset); with an id, that achievement becomes the selected one.

import { config } from './config.js';
import { createPopupFrame } from './popup-frame.js';
import { listAchievements, latestUnlocked } from './achievements.js';

const settings = config.board;
const words = settings.words;

export function createBoardPopup(canvas, { bottomInset, layout, badges }) {
  const { popup: spec } = layout;
  const frame = createPopupFrame(canvas, {
    bottomInset, className: 'ab', w: spec.w, h: spec.h, label: words.label,
    backdrop: spec.colors.backdrop, fadeMs: settings.fadeMs, minCssPxPerArtPx: settings.minCssPxPerArtPx,
  });
  const { backdrop, popup, art } = frame;
  for (const [name, value] of Object.entries(spec.colors)) backdrop.style.setProperty(`--ab-${name.replaceAll('_', '-')}`, value);
  backdrop.style.setProperty('--ab-badges', `url("${config.achievements.artDir + badges.file}")`);
  backdrop.style.setProperty('--ab-badge-w', badges.frame_w);
  backdrop.style.setProperty('--ab-badge-h', badges.frame_h);
  backdrop.style.setProperty('--ab-badge-frames', badges.locked_frame + 1);

  // ── Art (art pixels, scaled with the frame) ──
  const dir = settings.artDir;
  const slotBadges = spec.slots.map((slot) => badge({ x: slot.badge_x, y: slot.badge_y }));
  const selectedFrame = image(dir + spec.selected_file, { x: 0, y: 0 });
  const { detail_badge_2x: big, progress_bar: bar } = spec.regions;
  const detailBadge = badge({ x: big.x, y: big.y }, 'ab-badge-2x');
  const fill = el('div', 'ab-fill');
  Object.assign(fill.style, { left: `${bar.x}px`, top: `${bar.y}px`, height: `${bar.h}px` });
  art.append(image(dir + spec.file, { x: 0, y: 0 }), ...slotBadges, selectedFrame, detailBadge, fill);

  // ── Text and controls (CSS units, over the art) ──
  const close = placed(el('button', 'ab-close'), spec.regions.close);
  close.type = 'button';
  close.setAttribute('aria-label', 'Close');
  close.addEventListener('click', frame.requestClose);

  const slotList = el('div', 'ab-slots');
  slotList.setAttribute('role', 'listbox');
  slotList.setAttribute('aria-label', words.label);
  const slotButtons = spec.slots.map((slot, index) => {
    const button = placed(el('button', 'ab-slot'), slot);
    button.type = 'button';
    button.setAttribute('role', 'option');
    button.append(el('span', 'ab-slot-badge'), el('span', 'ab-slot-name'));
    button.addEventListener('click', () => select(index, { focus: true }));
    slotList.append(button);
    return button;
  });
  popup.addEventListener('keydown', (event) => {
    const next = neighbour(spec.slots, selected, event.key);
    if (next === null) return;
    event.preventDefault();
    select(next, { focus: true });
  });

  const note = el('div', 'ab-note');
  note.setAttribute('aria-live', 'polite');
  const name = placed(el('p', 'ab-region ab-name'), spec.regions.detail_name);
  const plainBadge = el('span', 'ab-plain-badge');   // the big badge, in the plain panel only
  const how = placed(el('div', 'ab-region ab-how'), spec.regions.detail_description);
  const reward = placed(el('div', 'ab-region ab-reward'), spec.regions.detail_reward);
  note.append(plainBadge, name, how, reward);
  const progressText = placed(el('p', 'ab-region ab-progress'), spec.regions.progress_text);

  popup.append(close, slotList, note, progressText);

  let selected = 0;

  function select(index, { focus = false } = {}) {
    selected = index;
    render();
    if (focus) slotButtons[index].focus({ preventScroll: true });
  }

  function render() {
    const all = listAchievements();
    const slot = spec.slots[selected];
    const [dx, dy] = spec.selected_offset;
    Object.assign(selectedFrame.style, { left: `${slot.x + dx}px`, top: `${slot.y + dy}px` });

    all.forEach((entry, index) => {
      const frameIndex = entry.unlocked ? entry.definition.badge_frame : badges.locked_frame;
      slotBadges[index]?.style.setProperty('--frame', frameIndex);
      const button = slotButtons[index];
      if (!button) return;
      button.style.setProperty('--frame', frameIndex);
      button.lastChild.textContent = entry.unlocked ? entry.definition.name : words.unknown;
      button.setAttribute('aria-selected', String(index === selected));
      button.tabIndex = index === selected ? 0 : -1;
    });

    const { definition, unlocked, count } = all[selected];
    const frameIndex = unlocked ? definition.badge_frame : badges.locked_frame;
    detailBadge.style.setProperty('--frame', frameIndex);
    plainBadge.style.setProperty('--frame', frameIndex);
    name.textContent = unlocked ? definition.name : words.unknown;
    how.replaceChildren(heading(words.how), ...howLines(definition, unlocked, count));
    reward.replaceChildren(heading(words.reward), el('p', 'ab-text', unlocked ? definition.reward : words.unknown));

    const earned = all.filter((entry) => entry.unlocked).length;
    fill.style.width = `${Math.floor(bar.w * earned / all.length)}px`;   // rounded down, as board.py draws it
    progressText.textContent = words.progress(earned, all.length);
  }

  // Not earned: the description only once there is some progress (with the
  // count, for countable ones); before that, nothing is given away.
  function howLines(definition, unlocked, count) {
    if (unlocked) return [el('p', 'ab-text', definition.desc)];
    if (!count || count.value <= 0) return [el('p', 'ab-text', words.undiscovered)];
    return [el('p', 'ab-text', definition.desc), el('p', 'ab-text ab-count', `${count.value} / ${count.goal}`)];
  }

  function indexOf(id) {
    return Math.max(0, listAchievements().findIndex((entry) => entry.definition.id === id));
  }

  return {
    show(onRequestClose) {
      select(indexOf(latestUnlocked()));
      frame.show(onRequestClose);
    },
    hide: frame.hide,
    refresh(selectId) {
      if (selectId) selected = indexOf(selectId);
      render();
    },
    isShown: frame.isShown,
  };
}

// Arrow keys: left and right step through the slots in reading order; up
// and down go to the nearest slot in the row above or below.
function neighbour(slots, from, key) {
  if (key === 'ArrowRight') return Math.min(slots.length - 1, from + 1);
  if (key === 'ArrowLeft') return Math.max(0, from - 1);
  if (key === 'Home') return 0;
  if (key === 'End') return slots.length - 1;
  if (key !== 'ArrowUp' && key !== 'ArrowDown') return null;
  const rows = [...new Set(slots.map((slot) => slot.y))].sort((a, b) => a - b);
  const row = rows[rows.indexOf(slots[from].y) + (key === 'ArrowDown' ? 1 : -1)];
  if (row === undefined) return from;
  const centre = (slot) => slot.x + slot.w / 2;
  return slots
    .map((slot, index) => ({ slot, index }))
    .filter(({ slot }) => slot.y === row)
    .sort((a, b) => Math.abs(centre(a.slot) - centre(slots[from])) - Math.abs(centre(b.slot) - centre(slots[from])))[0].index;
}

function heading(text) {
  return el('h3', 'ab-heading', text);
}

// One badge from the sheet, at an art-pixel position; --frame picks which.
function badge({ x, y }, extra = '') {
  const node = el('div', `ab-badge ${extra}`.trim());
  Object.assign(node.style, { left: `${x}px`, top: `${y}px` });
  return node;
}

// Puts an element on a rectangle of the pop-up art (in art pixels); CSS
// multiplies by --u, the size of one art pixel in CSS pixels.
function placed(node, { x, y, w, h }) {
  Object.entries({ '--x': x, '--y': y, '--rw': w, '--rh': h })
    .forEach(([name, value]) => node.style.setProperty(name, value));
  return node;
}

function image(src, { x, y }) {
  const img = document.createElement('img');
  img.src = src;
  img.alt = '';
  Object.assign(img.style, { left: `${x}px`, top: `${y}px` });
  return img;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
