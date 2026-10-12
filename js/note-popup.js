// note-popup.js — the welcome note, opened from the folded note on the sill:
// a small sheet of paper over the scene with a few lines from whoever left
// it. Words in backticks in the content file (`help`, `whoami`) become
// buttons that close the note and put that command on the prompt. There is
// no art: the paper is drawn in CSS, darker at night.
// The backdrop, scaling, plain fallback and closing are js/popup-frame.js.
// Exports: createNotePopup(canvas, { bottomInset, onCommand })
//            -> { show(onRequestClose, { night }), hide() }
//   onRequestClose() is called on the X, Escape, a click outside, or a
//   command in the note; the caller decides when to actually hide().
//   onCommand(word) is called after that for a command.

import { config } from './config.js';
import { createPopupFrame } from './popup-frame.js';
import { loadJson } from './assets.js';

const settings = config.welcomeNote;

export function createNotePopup(canvas, { bottomInset, onCommand }) {
  const ready = loadJson(settings.contentFile).then((content) => {
    const [w, h] = settings.size;
    const frame = createPopupFrame(canvas, {
      bottomInset, className: 'wn', w, h, label: content.label,
      backdrop: settings.backdrop, fadeMs: settings.fadeMs, minCssPxPerArtPx: settings.minCssPxPerArtPx,
    });
    fill(frame, content, onCommand);
    return frame;
  });

  async function show(onRequestClose, { night }) {
    const frame = await ready;
    frame.popup.classList.toggle('is-night', night);
    frame.show(onRequestClose);
  }

  async function hide() {
    (await ready).hide();
  }

  return { show, hide };
}

function fill({ popup, requestClose }, content, onCommand) {
  const close = el('button', 'wn-close', '✕');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close');
  close.addEventListener('click', requestClose);

  const command = (word) => {
    requestClose();
    onCommand(word);
  };
  const body = el('div', 'wn-body');
  for (const line of content.lines) body.append(paragraph(line, command));
  body.append(el('p', 'wn-signature', content.signature));
  popup.append(close, body);
}

// One line of the note; `word` in backticks becomes a command button.
function paragraph(text, onCommand) {
  const p = el('p', 'wn-line');
  text.split(/`([^`]+)`/).forEach((part, i) => {
    if (i % 2 === 0) {
      if (part) p.append(part);
      return;
    }
    const button = el('button', 'wn-command');
    button.type = 'button';
    button.append(el('code', '', part));
    button.addEventListener('click', () => onCommand(part));
    p.append(button);
  });
  return p;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
