// terrarium-journal.js — the field journal the wall pot opens: four tabs
// (the pot, the seed store, the crossing bench, the species codex) drawn on
// the scene canvas, over everything, in the journal's own 3x5 pixel font.
// Every position is from anim/terrarium/terrarium_brief.md §3, in pixels
// from the panel's top-left; the panel itself sits where the manifest puts
// terrarium_journal. The sprites are chrome, the words are drawn here.
// It reads the state every frame, so anything the terminal changes shows at
// once, on whatever tab is open.
// Hover swaps a slot or button to its hover frame; nothing moves.
// Closing: Escape, a click outside the panel (the pot on the wall included).
// Exports: createJournal(assets, terrarium) -> { open(tab), close(), isOpen(),
//            draw(ctx, time), pointer: { contains, setHovered, move, click, cursor } }

import { config } from './config.js';
import { inRect } from './geometry.js';
import { SPECIES, CROSSES, speciesIndex } from './terrarium-species.js';
import { TRAITS } from './terrarium.js';

const settings = config.terrarium;
const words = settings.words;
const HUE_DEG = { 1: -40, 2: -20, 3: 0, 4: 20, 5: 40 };   // bloom pixels only
const TILE_COLUMN = { seed: 0, sprout: 1, stem: 2, stem_leaves: 3, stem_leaf_l: 4, stem_leaf_r: 5, crown: 6, dead: 7, wilt: 8 };
const BLOOM_STAGE = { bud: 0, opening: 1, full: 2 };
const DEAD_STALK_TOP = 4;   // the first row of the withered tile's stalk
const SLOT = { empty: 0, hover: 1, filled: 2, locked: 3 };
const BUTTON = { normal: 0, hover: 1, disabled: 2 };

// Brief §3, panel-local.
const POT = { x: 12, y: 54 };                  // both pot halves
const BUTTONS_Y = 104;
const seedSlot = (i) => ({ x: 14 + (i % 6) * 22, y: 26 + Math.floor(i / 6) * 26, w: 16, h: 16 });
const codexSlot = (i) => ({ x: 13 + (i % 6) * 22, y: 26 + Math.floor(i / 6) * 30, w: 16, h: 16 });
const BENCH = [{ x: 20, y: 32, w: 20, h: 20 }, { x: 60, y: 32, w: 20, h: 20 }, { x: 108, y: 32, w: 20, h: 20 }];

export function createJournal(assets, terrarium) {
  const sheet = (name) => assets.animation(`terrarium_${name}`);
  const art = Object.fromEntries(['journal', 'tab_active', 'tabicons', 'seeds', 'codex', 'slot_sm', 'slot_lg', 'meter',
    'btn_sm', 'btn_lg', 'traits', 'stars', 'plants', 'blooms', 'pot_back', 'pot_front', 'font'].map((n) => [n, sheet(n)]));
  const panelInfo = art.journal.info;
  const PX = panelInfo.placement.x, PY = panelInfo.placement.y;
  const panel = { x: PX, y: PY, w: panelInfo.frame_w, h: panelInfo.frame_h };
  const tabs = panelInfo.tab_ys.map((y) => ({ x: panelInfo.paper_w, y, w: panelInfo.tab_w, h: panelInfo.tab_h }));
  const font = { charset: art.font.info.charset, w: art.font.info.frame_w, h: art.font.info.frame_h, advance: art.font.info.advance };
  const potInfo = art.pot_back.info;

  let open = false;
  let mouse = null;            // canvas pixels, while over the canvas
  let seedPick = -1;           // the Seeds tab's selected slot
  let codexPick = -1;
  let parents = [null, null];  // the crossing bench
  let picking = -1;            // 0 or 1 while choosing a parent from the seed grid
  let lastCross = null;        // the last roll, until the parents change

  document.addEventListener('keydown', (event) => {
    if (open && event.key === 'Escape') close();
  });

  function openAt(tab = terrarium.get().tab) {
    terrarium.tick();
    terrarium.setTab(tab);
    picking = -1;
    open = true;
  }
  function close() {
    open = false;
    picking = -1;
  }

  // ── drawing helpers (ctx is already translated to the panel) ──
  const tinted = new Map();   // colour -> the font sheet in that colour
  function fontIn(colour) {
    if (!tinted.has(colour)) {
      const source = art.font.imageFor('day');
      const c = document.createElement('canvas');
      c.width = source.width;
      c.height = source.height;
      const cx = c.getContext('2d');
      cx.drawImage(source, 0, 0);
      cx.globalCompositeOperation = 'source-in';
      cx.fillStyle = colour;
      cx.fillRect(0, 0, c.width, c.height);
      tinted.set(colour, c);
    }
    return tinted.get(colour);
  }
  function text(ctx, s, x, y, colour) {
    const glyphs = fontIn(colour);
    s = String(s).toUpperCase();
    for (let i = 0; i < s.length; i++) {
      const g = font.charset.indexOf(s[i]);
      if (g > 0) ctx.drawImage(glyphs, g * font.w, 0, font.w, font.h, x + i * font.advance, y, font.w, font.h);
    }
  }
  const textWidth = (s) => String(s).length * font.advance - 1;
  const centred = (ctx, s, cx, y, colour) => text(ctx, s, cx - (textWidth(s) >> 1), y, colour);

  function frame(ctx, time, name, index, x, y) {
    const { frame_w: w, frame_h: h } = art[name].info;
    ctx.drawImage(art[name].imageFor(time), index * w, 0, w, h, x, y, w, h);
  }
  function meterRow(ctx, time, row, x, y) {
    const { frame_w: w, frame_h: h } = art.meter.info;
    ctx.drawImage(art.meter.imageFor(time), 0, row * h, w, h, x, y, w, h);
  }
  function stars(ctx, time, rarity, x, y) {
    for (let i = 0; i < 5; i++) frame(ctx, time, 'stars', i < rarity ? 1 : 0, x + i * 8, y);
  }

  // Panel-local mouse position, or null.
  function local() {
    return mouse && { x: mouse.x - PX, y: mouse.y - PY };
  }
  const over = (rect) => { const m = local(); return !!m && inRect(m.x, m.y, rect); };

  // A button: its rect, label, whether it works, and what it does.
  function button(x, label, enabled, action, wide = false) {
    return { rect: { x, y: BUTTONS_Y, w: wide ? 48 : 40, h: 16 }, label, enabled, action, wide };
  }
  function drawButton(ctx, time, colours, b) {
    const state = !b.enabled ? BUTTON.disabled : over(b.rect) ? BUTTON.hover : BUTTON.normal;
    frame(ctx, time, b.wide ? 'btn_lg' : 'btn_sm', state, b.rect.x, b.rect.y);
    centred(ctx, b.label, b.rect.x + b.rect.w / 2, BUTTONS_Y + 6, b.enabled ? colours.text : colours.text_d);
  }

  // ── the plant (brief §8) ──
  // Foliage tiles stack up from the soil line; a bloom sits on the stem tile
  // below it, 4px to the left. The hue gene turns the bloom's pixels only.
  // The withered tile's stalk starts 4 rows down, so dead tiles overlap by
  // that much, or the stalk would have gaps.
  const hued = new Map();
  function bloomTile(time, row, stage, hue) {
    const key = `${time}|${row}|${stage}|${hue}`;
    if (!hued.has(key)) {
      const { frame_w: w, frame_h: h } = art.blooms.info;
      const c = document.createElement('canvas');
      c.width = w;
      c.height = h;
      const cx = c.getContext('2d', { willReadFrequently: true });
      cx.drawImage(art.blooms.imageFor(time), stage * w, row * h, w, h, 0, 0, w, h);
      if (HUE_DEG[hue]) rotateHue(cx, w, h, HUE_DEG[hue], row);
      hued.set(key, c);
    }
    return hued.get(key);
  }
  // The stem stub is in the bloom tile too: keep the colours the plant
  // sheet uses for the stem, rotate everything else.
  function rotateHue(cx, w, h, degrees, row) {
    const stem = stemColours(row);
    const image = cx.getImageData(0, 0, w, h);
    const d = image.data;
    for (let i = 0; i < d.length; i += 4) {
      if (!d[i + 3] || stem.has((d[i] << 16) | (d[i + 1] << 8) | d[i + 2])) continue;
      [d[i], d[i + 1], d[i + 2]] = shiftHue(d[i], d[i + 1], d[i + 2], degrees);
    }
    cx.putImageData(image, 0, 0);
  }
  const stemSets = new Map();
  function stemColours(row) {
    // The plain stem tile (column 2) of this species, in every time of day.
    if (!stemSets.has(row)) {
      const set = new Set();
      const t = art.plants.info.frame_w;
      const c = document.createElement('canvas');
      c.width = t;
      c.height = t;
      const cx = c.getContext('2d', { willReadFrequently: true });
      for (const time of config.times) {
        cx.clearRect(0, 0, t, t);
        cx.drawImage(art.plants.imageFor(time), TILE_COLUMN.stem * t, row * t, t, t, 0, 0, t, t);
        const d = cx.getImageData(0, 0, t, t).data;
        for (let i = 0; i < d.length; i += 4) if (d[i + 3]) set.add((d[i] << 16) | (d[i + 1] << 8) | d[i + 2]);
      }
      stemSets.set(row, set);
    }
    return stemSets.get(row);
  }

  function drawPlant(ctx, time, pot) {
    const row = speciesIndex(pot.species);
    const t = art.plants.info.frame_w;
    const x = POT.x + potInfo.centre_x - t / 2;           // stem columns 7-8 land on the pot's centre
    let top = POT.y + potInfo.soil_line - (t - 1);       // the bottom tile's last row is the soil line
    for (const [i, tile] of pot.stack.entries()) {
      if (tile in BLOOM_STAGE) {
        const { frame_w: bw, frame_h: bh } = art.blooms.info;
        ctx.drawImage(bloomTile(time, row, BLOOM_STAGE[tile], pot.genome.hue), x - 4, top + t - bh, bw, bh);
        break;
      }
      ctx.drawImage(art.plants.imageFor(time), TILE_COLUMN[tile] * t, row * t, t, t, x, top, t, t);
      if (i < pot.stack.length - 1) top -= tile === 'dead' ? t - DEAD_STALK_TOP : t;
    }
  }

  // ── tabs ──
  // Each returns its clickable parts for this frame: [{ rect, action }].
  function drawPotTab(ctx, time, colours) {
    const pot = terrarium.get().pot;
    frame(ctx, time, 'pot_back', 0, POT.x, POT.y);
    if (pot) drawPlant(ctx, time, pot);
    frame(ctx, time, 'pot_front', 0, POT.x, POT.y);

    const species = pot && SPECIES[speciesIndex(pot.species)];
    text(ctx, species ? species.name : 'Empty pot', 66, 21, colours.text);
    if (species) stars(ctx, time, species.rarity, 66, 30);
    text(ctx, terrarium.status(pot), 66, 41, colours.text_d);
    text(ctx, 'Water', 66, 50, colours.text_d);
    meterRow(ctx, time, pot ? Math.min(4, Math.ceil(pot.hydration * 4)) : 0, 66, 58);
    text(ctx, 'Growth', 66, 68, colours.text_d);
    meterRow(ctx, time, 5 + (pot ? Math.min(4, Math.floor(pot.growth * 4)) : 0), 66, 76);

    const alive = pot && !pot.dead;
    const buttons = [
      button(12, 'Water', !!alive, () => terrarium.water()),
      button(56, 'Trim', !!alive && pot.growth >= settings.trimFrom, () => terrarium.trim()),
      button(100, pot?.dead ? 'Clear' : 'Harvest', !!pot && (pot.dead || pot.growth >= 1), () => terrarium.harvest()),
    ];
    for (const b of buttons) drawButton(ctx, time, colours, b);
    return buttons.filter((b) => b.enabled);
  }

  // The seed grid: slot i is species i; owned kinds show their seed and how
  // many. `available(id)` is how many can be used (the bench holds some back).
  function drawSeedGrid(ctx, time, colours, selected, available, onPick) {
    const parts = [];
    SPECIES.forEach((species, i) => {
      const rect = seedSlot(i);
      const n = available(species.id);
      const state = n ? (i === selected || over(rect) ? SLOT.hover : SLOT.filled) : SLOT.empty;
      frame(ctx, time, 'slot_sm', state, rect.x, rect.y);
      if (!n) return;
      frame(ctx, time, 'seeds', i, rect.x + 4, rect.y + 4);
      text(ctx, n, rect.x + 12 - (String(n).length - 1) * font.advance, rect.y + 10, colours.text);
      parts.push({ rect, action: () => onPick(i) });
    });
    return parts;
  }

  // Name, then its rarity stars after it (never under a long name).
  function nameAndStars(ctx, time, colours, species, x, y, starsX) {
    text(ctx, species.name, x, y, colours.text);
    stars(ctx, time, species.rarity, Math.max(starsX, x + textWidth(species.name) + 4), y - 1);
  }

  function drawSeedsTab(ctx, time, colours) {
    const parts = drawSeedGrid(ctx, time, colours, seedPick, terrarium.count, (i) => { seedPick = i; });
    const species = SPECIES[seedPick];
    if (species && terrarium.count(species.id)) {
      nameAndStars(ctx, time, colours, species, 13, 76, 40);
      text(ctx, species.blurb, 13, 86, colours.text_d);
    } else {
      text(ctx, 'Pick a seed to plant.', 13, 76, colours.text_d);
    }
    const pot = terrarium.get().pot;
    const canPlant = !!species && terrarium.count(species.id) > 0 && !pot;
    const plant = button(100, 'Plant', canPlant, () => {
      if (terrarium.plant(species.id).ok) terrarium.setTab(0);
    });
    drawButton(ctx, time, colours, plant);
    if (pot && species) text(ctx, 'The pot is in use.', 13, 108, colours.text_d);
    return canPlant ? [...parts, plant] : parts;
  }

  // How many of a kind the bench may still take for parent `which`.
  function benchAvailable(which) {
    return (id) => terrarium.count(id) - (parents[1 - which] === id ? 1 : 0);
  }

  function drawCrossTab(ctx, time, colours) {
    // Picking a parent: the seed grid takes over the bench.
    if (picking >= 0) {
      const parts = drawSeedGrid(ctx, time, colours, -1, benchAvailable(picking), (i) => {
        parents[picking] = SPECIES[i].id;
        lastCross = null;
        picking = -1;
      });
      text(ctx, `Choose parent ${picking ? 'B' : 'A'}.`, 13, 76, colours.text);
      text(ctx, 'Click the page to cancel.', 13, 86, colours.text_d);
      // The page under the grid cancels; parts later in the list win a click.
      return [{ rect: { x: 0, y: 0, w: panelInfo.paper_w, h: panel.h }, action: () => { picking = -1; } }, ...parts];
    }

    // A parent you no longer have enough of drops off the bench.
    parents = parents.map((id, which) => (id && benchAvailable(which)(id) < 1 ? null : id));
    const [a, b] = parents;
    const prediction = a && b ? terrarium.predict(a, b) : null;
    const shown = lastCross ? lastCross.species : prediction?.hybrid ?? null;
    const parts = [];
    [a, b, shown].forEach((id, slot) => {
      const rect = BENCH[slot];
      const isParent = slot < 2;
      const state = slot === 2 ? (lastCross ? 2 : shown ? 1 : 0) : id ? 2 : over(rect) ? 1 : 0;
      frame(ctx, time, 'slot_lg', state, rect.x, rect.y);
      if (id) frame(ctx, time, 'seeds', speciesIndex(id), rect.x + 6, rect.y + 6);
      if (id) {
        const species = SPECIES[speciesIndex(id)];
        centred(ctx, species.short ?? species.name, rect.x + 10, 55, colours.text);
      }
      if (isParent) parts.push({ rect, action: () => { picking = slot; } });
    });
    text(ctx, 'x', 46, 39, colours.text_d);
    text(ctx, '>', 90, 39, colours.text_d);

    // The traits the offspring would get (or did get), and its rarity.
    const genome = lastCross?.genome ?? prediction?.genome;
    const rarityOf = shown ?? (a && b ? [a, b].sort((p, q) => SPECIES[speciesIndex(q)].rarity - SPECIES[speciesIndex(p)].rarity)[0] : null);
    [...TRAITS, 'rarity'].forEach((trait, i) => {
      const x = 14 + i * 22;
      frame(ctx, time, 'traits', i, x, 66);
      const value = trait === 'rarity' ? (rarityOf ? SPECIES[speciesIndex(rarityOf)].rarity : '-') : genome?.[trait] ?? '-';
      text(ctx, value, x + 9, 68, colours.text);
    });

    let line = 'Pick two seeds to cross.';
    if (lastCross) line = lastCross.line;
    else if (prediction?.hybrid) line = `Chance ${Math.round(prediction.chance * 100)}% - new species`;
    else if (prediction) line = 'No new species from this pair';
    text(ctx, line, 13, 84, colours.text_d);

    const go = button(52, 'Cross', !!prediction, () => {
      const result = terrarium.cross(a, b);
      if (!result.ok) return;
      const name = SPECIES[speciesIndex(result.species)].name;
      lastCross = {
        species: result.species,
        genome: terrarium.get().seeds[result.species].at(-1),
        line: result.hit ? `New species: ${name}!` : `You got ${/^[aeiou]/i.test(name) ? 'an' : 'a'} ${name} seed.`,
      };
    }, true);
    drawButton(ctx, time, colours, go);
    return prediction ? [...parts, go] : parts;
  }

  function drawCodexTab(ctx, time, colours) {
    const found = new Set(terrarium.get().codex);
    const parts = [];
    SPECIES.forEach((species, i) => {
      const rect = codexSlot(i);
      const known = found.has(species.id);
      frame(ctx, time, 'slot_sm', known ? (i === codexPick || over(rect) ? SLOT.hover : SLOT.filled) : SLOT.locked, rect.x, rect.y);
      if (known) frame(ctx, time, 'codex', i, rect.x, rect.y);
      parts.push({ rect, action: () => { codexPick = i; } });
    });
    text(ctx, `${found.size} / ${SPECIES.length} discovered`, 13, 80, colours.text);
    const species = SPECIES[codexPick];
    if (species && found.has(species.id)) {
      nameAndStars(ctx, time, colours, species, 13, 90, 60);
      text(ctx, species.flavour, 13, 112, colours.text_d);
    } else {
      if (species) text(ctx, '???', 13, 90, colours.text);
      const line = species ? hint(species, found)
        : found.size === 0 ? 'Harvest a plant to start it.'
        : found.size === SPECIES.length ? 'Every species found.' : 'Cross seeds to find the rest';
      text(ctx, line, 13, 112, colours.text_d);
    }
    return parts;
  }

  // An undiscovered page: a starter is grown, a hybrid is bred; the
  // recipe shows once both of its parents are in the codex.
  function hint(species, found) {
    const recipe = CROSSES.find((cross) => cross.out === species.id);
    if (!recipe) return 'Grow one to fill this page.';
    return found.has(recipe.a) && found.has(recipe.b) ? `Try ${nameOf(recipe.a)} x ${nameOf(recipe.b)}` : 'Cross seeds to find the rest';
  }

  const TAB_DRAW = [drawPotTab, drawSeedsTab, drawCrossTab, drawCodexTab];
  let parts = [];   // this frame's clickable parts, panel-local

  function draw(ctx, time) {
    if (!open) return;
    const tab = terrarium.get().tab;
    const colours = settings.colours[time];
    ctx.translate(PX, PY);
    ctx.drawImage(art.journal.imageFor(time), 0, 0);
    ctx.drawImage(art.tab_active.imageFor(time), tabs[tab].x, tabs[tab].y);
    tabs.forEach((t, i) => frame(ctx, time, 'tabicons', i, t.x + 1, t.y + 6));
    text(ctx, words.titles[tab], 13, 7, colours.accent);
    parts = TAB_DRAW[tab](ctx, time, colours);
    tabs.forEach((rect, i) => parts.push({ rect, action: () => { terrarium.setTab(i); picking = -1; } }));
  }

  // The topmost part under a panel-local point.
  const partAt = (x, y) => [...parts].reverse().find((p) => inRect(x, y, p.rect)) ?? null;

  return {
    open: openAt,
    close,
    isOpen: () => open,
    draw,
    pointer: {
      // While open it takes every click: outside the panel closes it.
      contains: () => open,
      setHovered(on) { if (!on) mouse = null; },
      move(x, y) { mouse = { x, y }; },
      click(x, y) {
        mouse = { x, y };
        if (!inRect(x, y, panel)) return close();
        partAt(x - PX, y - PY)?.action();
      },
      cursor(x, y) {
        return inRect(x, y, panel) && partAt(x - PX, y - PY) ? 'pointer' : '';
      },
    },
  };
}

function nameOf(id) {
  const species = SPECIES[speciesIndex(id)];
  return species.short ?? species.name;
}

// Hue rotation of one colour, in HSL, keeping lightness and saturation.
function shiftHue(r, g, b, degrees) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [r * 255, g * 255, b * 255];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = ((h * 60 + degrees) % 360 + 360) % 360 / 360;
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const channel = (t) => {
    t = (t + 1) % 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  return [channel(h + 1 / 3), channel(h), channel(h - 1 / 3)].map((v) => Math.round(v * 255));
}
