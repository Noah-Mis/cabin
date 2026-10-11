// unlock-sign.js — the wooden sign that slides down near the top of the view
// when an achievement is earned: the badge in its slot and the name as real
// text in its blank area. Unlocks queue up, so two at once show one after
// the other. It is drawn at the canvas's whole-number pixel scale, lined up
// with the scene, like the folder pop-up.
// Exports: createUnlockSign(canvas, { manifest, openingY }) -> { show(definition), clear() }

import { config } from './config.js';

export function createUnlockSign(canvas, { manifest, openingY }) {
  const settings = config.achievements.sign;
  const { sign, badges } = manifest;
  const [canvasW] = manifest.canvas;
  const signX = Math.floor((canvasW - sign.w) / 2);
  const signY = openingY + settings.marginTopPx;

  const root = el('div', 'us');
  root.setAttribute('role', 'status');
  root.setAttribute('aria-live', 'polite');
  root.style.setProperty('--us-slide', `${settings.slideMs}ms`);
  root.style.setProperty('--us-text', settings.textColour);
  const art = el('div', 'us-art');
  const board = el('img', 'us-board');
  board.src = config.achievements.artDir + sign.file;
  board.alt = '';
  const badge = el('div', 'us-badge');
  Object.assign(badge.style, {
    left: `${sign.badge_slot.x}px`, top: `${sign.badge_slot.y}px`,
    width: `${badges.frame_w}px`, height: `${badges.frame_h}px`,
    backgroundImage: `url("${config.achievements.artDir + badges.file}")`,
  });
  art.append(board, badge);
  const label = el('p', 'us-label', 'achievement unlocked');
  const name = el('p', 'us-name');
  const text = el('div', 'us-text');
  text.append(label, name);
  root.append(art, text);
  root.hidden = true;
  document.body.append(root);

  const queue = [];
  let timer = null;

  // Same scale and alignment as the canvas, in device pixels.
  function place() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const scale = Math.round(rect.width * dpr / canvas.width);
    const u = scale / dpr;
    const left = Math.round(rect.left * dpr) + signX * scale;
    const top = Math.round(rect.top * dpr) + signY * scale;
    root.style.setProperty('--u', `${u}px`);
    root.style.setProperty('--hide-y', `${-(signY + sign.h) * u}px`);
    root.style.left = '0px';
    root.style.top = '0px';
    root.style.translate = `${left / dpr}px ${top / dpr}px`;
    art.style.transform = `scale(${u})`;
    Object.assign(text.style, {
      left: `${sign.text_area.x * u}px`, top: `${sign.text_area.y * u}px`,
      width: `${sign.text_area.w * u}px`, height: `${sign.text_area.h * u}px`,
    });
    // The longest name has to fit on one line of the text area.
    const chars = Math.max(name.textContent.length, label.textContent.length * 0.6);
    const fit = (sign.text_area.w * u) / (chars * 0.62);
    name.style.fontSize = `${Math.min(u * 5.5, fit)}px`;
    label.style.fontSize = `${Math.min(u * 3.2, fit * 0.6)}px`;
  }

  function showNext() {
    const definition = queue.shift();
    if (!definition) { timer = null; return; }
    name.textContent = definition.name;
    badge.style.backgroundPosition = `${-definition.badge_frame * badges.frame_w}px 0`;
    root.hidden = false;
    root.classList.remove('is-down');
    place();
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add('is-down')));
    timer = setTimeout(() => {
      root.classList.remove('is-down');
      timer = setTimeout(() => { root.hidden = true; showNext(); }, settings.slideMs);
    }, settings.slideMs + settings.showMs);
  }

  window.addEventListener('resize', () => { if (!root.hidden) place(); });

  return {
    show(definition) {
      queue.push(definition);
      if (!timer) showNext();
    },
    clear() {
      queue.length = 0;
      clearTimeout(timer);
      timer = null;
      root.classList.remove('is-down');
      root.hidden = true;
    },
  };
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
