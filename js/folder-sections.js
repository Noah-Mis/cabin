// folder-sections.js — turns the content file's sections into HTML. Knows
// nothing about where they go. A section is { heading, and any of: text
// (paragraphs), items ({ title, meta, points }), bullets, tags, links
// ({ label, value?, href }) }. Words are used exactly as written in the file.
// Exports: renderSections(sections) -> DocumentFragment
//          renderLink({ label, value, href }) -> <a>

export function renderSections(sections) {
  const fragment = document.createDocumentFragment();
  for (const section of sections) fragment.append(renderSection(section));
  return fragment;
}

function renderSection(section) {
  const block = el('section', 'fp-section');
  if (section.heading) block.append(el('h3', 'fp-heading', section.heading));
  for (const paragraph of section.text ?? []) block.append(el('p', 'fp-text', paragraph));
  for (const item of section.items ?? []) block.append(renderItem(item));
  if (section.bullets?.length) block.append(renderBullets(section.bullets));
  if (section.tags?.length) {
    const tags = el('ul', 'fp-tags');
    for (const tag of section.tags) tags.append(el('li', 'fp-tag', tag));
    block.append(tags);
  }
  if (section.links?.length) {
    const links = el('ul', 'fp-links');
    for (const link of section.links) links.append(wrap('li', renderLink(link)));
    block.append(links);
  }
  return block;
}

function renderItem({ title, meta, points }) {
  const item = el('div', 'fp-item');
  item.append(el('p', 'fp-item-title', title));
  if (meta) item.append(el('p', 'fp-meta', meta));
  if (points?.length) item.append(renderBullets(points));
  return item;
}

function renderBullets(lines) {
  const list = el('ul', 'fp-bullets');
  for (const line of lines) list.append(el('li', '', line));
  return list;
}

// "Label: value" when both are given, otherwise just the label.
export function renderLink({ label, value, href }) {
  const link = el('a', 'fp-link', value ? `${label}: ${value}` : label);
  link.href = href;
  if (/^https?:/.test(href)) {
    link.target = '_blank';
    link.rel = 'noopener';
  } else if (href.toLowerCase().endsWith('.pdf')) {
    link.download = '';   // the résumé: offer it as a download
  }
  return link;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function wrap(tag, child) {
  const node = document.createElement(tag);
  node.append(child);
  return node;
}
