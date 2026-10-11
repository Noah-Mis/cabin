// folder-popup.js — the pop-up that opens from the folder on the sill: the
// same folder lying open, drawn at a whole-number pixel scale like the
// canvas, with real HTML text laid over its blank regions (so it can be
// selected, read by screen readers, and edited in the content file).
// Positions and sizes come from the layout file, words from the content file.
// When the folder would be too small to read, the same content is shown in a
// plain single-column panel instead.
// Exports: createFolderPopup(canvas, { bottomInset })
//            -> { show(onRequestClose), hide() }
//   onRequestClose() is called on the X, Escape, or a click outside; the
//   caller decides when to actually hide().

import { config } from './config.js';
import { renderSections, renderLink } from './folder-sections.js';
import { track } from './achievements.js';

const settings = config.folderPopup;

export function createFolderPopup(canvas, { bottomInset }) {
  const ready = Promise.all([loadJson(settings.layoutFile), loadJson(settings.contentFile)])
    .then(([layout, content]) => build(layout, content));
  let requestClose = () => {};
  let shown = false;

  function build(layout, content) {
    const parts = buildDom(layout, content, () => requestClose());
    document.body.append(parts.backdrop);
    window.addEventListener('resize', () => { if (shown) place(parts, layout); });
    document.addEventListener('keydown', (event) => {
      if (shown && event.key === 'Escape') requestClose();
    });
    return parts;
  }

  async function show(onRequestClose) {
    requestClose = onRequestClose;
    const parts = await ready;
    shown = true;
    parts.selectTab(settings.firstTab);
    parts.backdrop.hidden = false;
    place(parts, parts.layout);
    requestAnimationFrame(() => parts.backdrop.classList.add('is-visible'));
    parts.popup.focus({ preventScroll: true });
  }

  async function hide() {
    const parts = await ready;
    shown = false;
    parts.backdrop.classList.remove('is-visible');
    setTimeout(() => { if (!shown) parts.backdrop.hidden = true; }, settings.fadeMs);
  }

  // Same whole-number scale as the canvas (device pixels per art pixel),
  // shrunk if needed to fit above the prompt line, and centred there.
  function place(parts, layout) {
    const dpr = window.devicePixelRatio || 1;
    const { w, h } = layout.popup;
    const canvasScale = Math.round(canvas.getBoundingClientRect().width * dpr / canvas.width);
    const availW = window.innerWidth * dpr;
    const availH = (window.innerHeight - bottomInset()) * dpr;
    const scale = Math.min(canvasScale, Math.floor(availW / w), Math.floor(availH / h));
    const cssPerArtPx = scale / dpr;
    const plain = scale < 1 || cssPerArtPx < settings.minCssPxPerArtPx;

    parts.popup.classList.toggle('is-plain', plain);
    parts.backdrop.style.setProperty('--prompt-h', `${bottomInset()}px`);
    if (plain) {
      parts.popup.style.transform = '';
      return;
    }
    const left = Math.floor((availW - w * scale) / 2);
    const top = Math.floor((availH - h * scale) / 2);
    // Transforms, not left/top, so the art lands exactly on device pixels.
    parts.popup.style.transform = `translate(${left / dpr}px, ${top / dpr}px)`;
    parts.popup.style.setProperty('--u', `${cssPerArtPx}px`);
    parts.art.style.transform = `scale(${cssPerArtPx})`;
  }

  return { show, hide };
}

function buildDom(layout, content, onClose) {
  const dir = settings.artDir;
  const backdrop = el('div', 'fp-backdrop');
  backdrop.hidden = true;
  backdrop.dataset.keepFocus = '';   // the terminal leaves focus alone in here
  setColours(backdrop, layout.colors);
  backdrop.addEventListener('click', (event) => { if (event.target === backdrop) onClose(); });

  const popup = el('div', 'fp');
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-modal', 'true');
  popup.setAttribute('aria-label', content.card.name);
  popup.tabIndex = -1;
  popup.style.setProperty('--w', layout.popup.w);
  popup.style.setProperty('--h', layout.popup.h);

  const art = el('div', 'fp-art');
  const folderImage = image(dir + layout.popup.file, layout.popup);
  const activeTab = image('', layout.tabs[0]);
  art.append(folderImage, activeTab);

  const close = placed(el('button', 'fp-close'), layout.regions.close);
  close.type = 'button';
  close.setAttribute('aria-label', 'Close');
  close.addEventListener('click', onClose);

  const { regions } = layout;
  const photo = placed(el('div', 'fp-region fp-photo'), regions.photo);
  const card = placed(buildCard(content.card), regions.card);
  const sticky = placed(buildSticky(content.sticky), regions.sticky);
  const stamp = placed(el('div', 'fp-region fp-stamp', content.stamp), regions.stamp);
  const page = placed(el('div', 'fp-region fp-page'), regions.page);
  page.setAttribute('role', 'tabpanel');
  page.tabIndex = 0;

  const tabList = el('div', 'fp-tabs');
  tabList.setAttribute('role', 'tablist');
  const tabButtons = {};
  for (const tab of layout.tabs) {
    const button = placed(el('button', 'fp-tab', tab.name), tab);
    button.type = 'button';
    button.setAttribute('role', 'tab');
    button.addEventListener('click', () => selectTab(tab.name));
    tabButtons[tab.name] = button;
    tabList.append(button);
  }

  function selectTab(name) {
    const tab = layout.tabs.find((t) => t.name === name);
    activeTab.src = dir + tab.active_file;
    Object.assign(activeTab.style, { left: `${tab.x}px`, top: `${tab.y}px` });
    for (const [tabName, button] of Object.entries(tabButtons)) {
      button.setAttribute('aria-selected', String(tabName === name));
    }
    page.replaceChildren(renderSections(content.tabs[name]));
    page.scrollTop = 0;
    track('tabsSeen', name);
  }

  popup.append(art, close, photo, card, sticky, stamp, tabList, page);
  backdrop.append(popup);
  return { backdrop, popup, art, page, selectTab, layout };
}

function buildCard({ header, name, lines }) {
  const card = el('div', 'fp-region fp-card');
  card.append(el('p', 'fp-card-header', header), el('p', 'fp-card-name', name));
  for (const line of lines) card.append(el('p', 'fp-card-line', line));
  return card;
}

function buildSticky({ title, links }) {
  const sticky = el('div', 'fp-region fp-sticky');
  sticky.append(el('p', 'fp-sticky-title', title));
  const list = el('ul', 'fp-sticky-links');
  for (const link of links) {
    const item = document.createElement('li');
    item.append(renderLink(link));
    list.append(item);
  }
  sticky.append(list);
  return sticky;
}

// Puts an element on a rectangle of the folder art (in art pixels); CSS
// multiplies by --u, the size of one art pixel in CSS pixels.
function placed(node, { x, y, w, h }) {
  Object.entries({ '--x': x, '--y': y, '--rw': w, '--rh': h })
    .forEach(([name, value]) => node.style.setProperty(name, value));
  return node;
}

function image(src, { x = 0, y = 0, w, h }) {
  const img = document.createElement('img');
  if (src) img.src = src;
  img.alt = '';
  Object.assign(img.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` });
  return img;
}

function setColours(node, colors) {
  for (const [name, value] of Object.entries(colors)) node.style.setProperty(`--fp-${name.replace('_', '-')}`, value);
  node.style.setProperty('--fp-link', settings.linkColour);
  node.style.setProperty('--fp-meta', settings.metaColour);
  node.style.setProperty('--fp-fade', `${settings.fadeMs}ms`);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function loadJson(url) {
  const response = await fetch(url, { cache: 'no-cache' });   // always pick up edited content
  if (!response.ok) throw new Error(`could not load ${url} (${response.status})`);
  return response.json();
}
