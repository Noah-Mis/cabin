// folder-popup.js — the pop-up that opens from the folder on the sill: the
// same folder lying open, drawn at a whole-number pixel scale like the
// canvas, with real HTML text laid over its blank regions (so it can be
// selected, read by screen readers, and edited in the content file).
// Positions and sizes come from the layout file, words from the content file.
// The backdrop, scaling, plain fallback and closing are js/popup-frame.js.
// Exports: createFolderPopup(canvas, { bottomInset })
//            -> { show(onRequestClose), hide() }
//   onRequestClose() is called on the X, Escape, or a click outside; the
//   caller decides when to actually hide().

import { config } from './config.js';
import { createPopupFrame } from './popup-frame.js';
import { renderSections, renderLink } from './folder-sections.js';
import { track } from './achievements.js';

const settings = config.folderPopup;

export function createFolderPopup(canvas, { bottomInset }) {
  const ready = Promise.all([loadJson(settings.layoutFile), loadJson(settings.contentFile)])
    .then(([layout, content]) => {
      const frame = createPopupFrame(canvas, {
        bottomInset, className: 'fp', w: layout.popup.w, h: layout.popup.h, label: content.card.name,
        backdrop: layout.colors.backdrop, fadeMs: settings.fadeMs, minCssPxPerArtPx: settings.minCssPxPerArtPx,
      });
      return { frame, ...fillFrame(frame, layout, content) };
    });

  async function show(onRequestClose) {
    const { frame, selectTab } = await ready;
    selectTab(settings.firstTab);
    frame.show(onRequestClose);
  }

  async function hide() {
    (await ready).frame.hide();
  }

  return { show, hide };
}

function fillFrame({ backdrop, popup, art, requestClose: onClose }, layout, content) {
  const dir = settings.artDir;
  setColours(backdrop, layout.colors);

  const folderImage = image(dir + layout.popup.file, layout.popup);
  const activeTab = image('', layout.tabs[0]);
  art.append(folderImage, activeTab);
  // Fetch every tab's art up front: switching tabs mid-download would
  // otherwise cancel it, leaving a blank tab (and a failed request).
  for (const tab of layout.tabs) new Image().src = dir + tab.active_file;

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

  popup.append(close, photo, card, sticky, stamp, tabList, page);
  return { selectTab };
}

function buildCard({ header, name, lines }) {
  const card = el('div', 'fp-region fp-card');
  card.append(el('p', 'fp-card-header', header), el('p', 'fp-card-name', name));
  for (const line of lines) card.append(el('p', 'fp-card-line', line));
  // Each line's length: on a sideways phone a long line shrinks to fit (style.css).
  for (const node of card.querySelectorAll('.fp-card-name, .fp-card-line')) node.style.setProperty('--chars', node.textContent.length);
  return card;
}

function buildSticky({ title, links }) {
  const sticky = el('div', 'fp-region fp-sticky');
  sticky.append(el('p', 'fp-sticky-title', title));
  const list = el('ul', 'fp-sticky-links');
  for (const link of links) {
    const item = document.createElement('li');
    item.append(renderLink(link));
    // Its longest unbreakable run (a line may wrap after a space or a hyphen):
    // on a sideways phone the link shrinks until that fits (style.css).
    const runs = item.textContent.split(/(?<=[\s-])/).map((run) => run.trim().length);
    item.style.setProperty('--chars', Math.max(...runs));
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
